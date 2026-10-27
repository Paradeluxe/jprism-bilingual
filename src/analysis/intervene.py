#!/usr/bin/env python3
"""intervene.py — jspace intervention tool: READ **and WRITE** the residual stream.

Give a fitted Jacobian lens a steering wheel: edit one hidden layer mid-forward,
then read out what changed (model top-k, lens readout across layers, optional
greedy generation).

Ops:      add (h += α·v) | proj_out (remove v̂ component) | scale (k·component)
          | swap (replace with the residual captured from another prompt)
Vectors:  --vec-token (input-embedding direction) | --vec-diff-a/b (hidden-state
          difference between two prompts, at the op layer) | --vec-file (.pt/.npy)
Modes:    single op | --probe (clean readout + lens trace) | --sweep (layer×alpha grid)

Examples:
  python intervene.py --model 0.6B --prompt "The capital of France is" --probe --watch-token " Paris"
  python intervene.py --model 0.6B --prompt "The capital of Italy is" \
      --op swap --layer 12 --swap-from "The capital of France is"
  python intervene.py --model 0.6B --prompt "The capital of France is" \
      --op add --layer 12 --vec-diff-a "The capital of France is" --vec-diff-b "The capital of Italy is" \
      --alpha 4 --gen 6 --report demo_add.json
  python intervene.py --model 0.6B --prompt "The capital of France is" \
      --op proj_out --layer 12 --vec-diff-a "The capital of France is" --vec-diff-b "The capital of Italy is"
  python intervene.py --model 0.6B --prompt "The capital of France is" \
      --sweep "layers=0:26:2,alphas=1,2,4,8" --vec-diff-a "..." --vec-diff-b "..." --report sweep.json
"""

from __future__ import annotations

import argparse
import json
import os
import time

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
if os.name == "nt":  # local Windows box; the cluster brings its own HF envs
    os.environ.setdefault("HF_HOME", r"E:\huggingface_cache")
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"E:\huggingface_cache\hub")
    os.environ.setdefault("TRANSFORMERS_CACHE", r"E:\huggingface_cache\hub")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import torch
import transformers
from jlens.hf import from_hf
from jlens.hooks import ActivationRecorder
from jlens.lens import JacobianLens

PROJECT = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")

LOCAL_MODELS = {
    "0.6B":     dict(hf_name="Qwen/Qwen3-0.6B",   local=r"E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B",   tag="qwen3-0.6b"),
    "1.7B":     dict(hf_name="Qwen/Qwen3-1.7B",   local=r"E:\huggingface_cache\manual\Qwen3-1.7B",              tag="qwen3-1.7b"),
    "3.5-0.8B": dict(hf_name="Qwen/Qwen3.5-0.8B", local=r"E:\huggingface_cache\hub\models--Qwen--Qwen3.5-0.8B", tag="qwen3.5-0.8b"),
    "3.5-2B":   dict(hf_name="Qwen/Qwen3.5-2B",   local=r"E:\huggingface_cache\hub\models--Qwen--Qwen3.5-2B",   tag="qwen3.5-2b"),
    "4B":       dict(hf_name="Qwen/Qwen3-4B",     local=r"E:\huggingface_cache\hub\models--Qwen--Qwen3-4B",     tag="qwen3-4b"),
}

# Cluster (SICC ~/jspace): weights under ~/models (bf16 8B/9B/14B/27B were
# removed in the 09-27 disk rescue; re-download on demand). Use --device cuda.
CLUSTER_MODELS = {
    "QQ06-Q4": dict(hf_name="unsloth/Qwen3-0.6B-GGUF", local=os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q4km"), tag="qwen3-0.6b-q4km", loader="gguf", gguf_file="Qwen3-0.6B-Q4_K_M.gguf"),
    "QQ06-Q2": dict(hf_name="unsloth/Qwen3-0.6B-GGUF", local=os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q2k"),  tag="qwen3-0.6b-q2k",  loader="gguf", gguf_file="Qwen3-0.6B-Q2_K.gguf"),
    "Q17-Q4":  dict(hf_name="unsloth/Qwen3-1.7B-GGUF", local=os.path.join(HOME, "models", "gguf", "qwen3-1.7b-q4km"), tag="qwen3-1.7b-q4km", loader="gguf", gguf_file="Qwen3-1.7B-Q4_K_M.gguf"),
    "Q17-Q2":  dict(hf_name="unsloth/Qwen3-1.7B-GGUF", local=os.path.join(HOME, "models", "gguf", "qwen3-1.7b-q2k"),  tag="qwen3-1.7b-q2k",  loader="gguf", gguf_file="Qwen3-1.7B-Q2_K.gguf"),
    "Q06-FP8": dict(hf_name="Qwen/Qwen3-0.6B-FP8", local=os.path.join(HOME, "models", "qwen3-0.6b-fp8"), tag="qwen3-0.6b-fp8"),
    "Q17-BNB": dict(hf_name="unsloth/Qwen3-1.7B-unsloth-bnb-4bit", local=os.path.join(HOME, "models", "qwen3-1.7b-bnb4"), tag="qwen3-1.7b-bnb4"),
    "Q4-AWQ":  dict(hf_name="Qwen/Qwen3-4B-AWQ", local=os.path.join(HOME, "models", "qwen3-4b-awq"), tag="qwen3-4b-awq"),
    "E2B":     dict(hf_name="google/gemma-4-E2B", local=os.path.join(HOME, "models", "gemma-4-E2B"), tag="gemma4-e2b", loader="image_text"),
}

MODELS = LOCAL_MODELS if os.name == "nt" else CLUSTER_MODELS


# ---------------------------------------------------------------- model / lens

def resolve_local(local: str) -> str:
    if os.path.isfile(os.path.join(local, "config.json")):
        return local
    snap = os.path.join(local, "snapshots")
    if os.path.isdir(snap):
        subs = [os.path.join(snap, d) for d in sorted(os.listdir(snap))]
        subs = [s for s in subs if os.path.isfile(os.path.join(s, "config.json"))]
        if subs:
            return subs[-1]
    return local


def load_model(key: str, device: str):
    cfg = MODELS[key]
    loader = cfg.get("loader", "causal")
    path = resolve_local(cfg["local"])
    dtype = torch.float32 if device == "cpu" else torch.bfloat16
    kw = {"local_files_only": True}
    if device == "cuda":
        kw["device_map"] = {"": 0}  # fits bnb/AWQ/gguf too; avoids .to() on quantized weights
    if loader == "gguf":
        kw["gguf_file"] = cfg["gguf_file"]
    if loader == "image_text":
        cls = getattr(transformers, "AutoModelForImageTextToText", None) or transformers.AutoModelForCausalLM
    else:
        cls = transformers.AutoModelForCausalLM
    try:
        loaded = cls.from_pretrained(path, dtype=dtype, **kw)
    except TypeError:  # older transformers
        loaded = cls.from_pretrained(path, torch_dtype=dtype, **kw)
    loaded.eval()
    if device == "cpu":
        loaded = loaded.to("cpu")
    tok_kw = {"local_files_only": True}
    if loader == "gguf":
        tok_kw["gguf_file"] = cfg["gguf_file"]
    tok = transformers.AutoTokenizer.from_pretrained(path, **tok_kw)
    wrapper = from_hf(loaded, tok)  # force_bos=True = fitting protocol
    return loaded, tok, wrapper


def load_lens(key: str, override: str | None):
    cfg = MODELS[key]
    if override:
        return JacobianLens.load(override) if os.path.isfile(override) else None
    p = os.path.join(PROJECT, "lenses", "local", cfg["tag"], "jlens_n1000_Lstep2_wikitext.pt")
    return JacobianLens.load(p) if os.path.isfile(p) else None


# ------------------------------------------------------------------ mechanisms

def make_writer(blocks, layer: int, fn, once: bool = False):
    """Register an EDIT hook; call fn(h[B,T,D]) -> h'. Register BEFORE any
    ActivationRecorder so the recorder (and the caller) see the edited stream.
    once=True: apply only on the first forward (prefill), then let it run free
    — the right mode for generation demos (avoids per-step re-injection)."""
    state = {"n": 0}

    def hook(module, args, output):
        state["n"] += 1
        if once and state["n"] > 1:
            return None  # passthrough: keep the original output
        if torch.is_tensor(output):
            return fn(output)
        return (fn(output[0]),) + tuple(output[1:])
    return blocks[layer].register_forward_hook(hook)


def op_add(vec, alpha, pos):
    def fn(h):
        h = h.clone()
        h[:, pos, :] = h[:, pos, :] + alpha * vec.to(h.dtype)
        return h
    return fn


def op_proj_out(vec, pos):
    v = (vec / (vec.norm() + 1e-9)).to(vec.dtype)
    def fn(h):
        h = h.clone()
        comp = h[:, pos, :] @ v
        h[:, pos, :] = h[:, pos, :] - comp.unsqueeze(-1) * v.to(h.dtype)
        return h
    return fn


def op_scale(vec, k, pos):
    v = (vec / (vec.norm() + 1e-9)).to(vec.dtype)
    def fn(h):
        h = h.clone()
        comp = h[:, pos, :] @ v
        h[:, pos, :] = h[:, pos, :] + (k - 1.0) * comp.unsqueeze(-1) * v.to(h.dtype)
        return h
    return fn


def op_swap(vec_src, pos):
    def fn(h):
        h = h.clone()
        h[:, pos, :] = vec_src.to(h.dtype)
        return h
    return fn


# -------------------------------------------------------------------- readouts

@torch.no_grad()
def capture(wrapper, blocks, prompt, layer, pos, max_len=256):
    """Clean forward; return the residual [D] at (layer, pos) as float32."""
    ids = wrapper.encode(prompt, max_length=max_len)
    with ActivationRecorder(blocks, at=[layer]) as rec:
        wrapper.forward(ids)
    return rec.activations[layer][0][pos].detach().float()


@torch.no_grad()
def readout(wrapper, blocks, lens, prompt, *, writer_fn=None, writer_layer=None,
            watch_layers, pos=-1, watch_id=None, max_len=256, topk=5):
    """Forward (optionally with an edit), then read model + lens top-k.

    Returns dict: model {top1, top1_prob, topk:[(tok,prob)...]},
                  lens_trace {layer: {top1, top1_prob, watch_rank, watch_prob}}
    """
    ids = wrapper.encode(prompt, max_length=max_len)
    final = wrapper.n_layers - 1
    at = sorted(set(list(watch_layers) + [final]))
    handle = make_writer(blocks, writer_layer, writer_fn) if writer_fn else None
    try:
        with ActivationRecorder(blocks, at=at) as rec:
            wrapper.forward(ids)
            acts = {i: rec.activations[i][0].detach().float() for i in rec.activations}
    finally:
        if handle is not None:
            handle.remove()

    def unembed_last(res):
        return wrapper.unembed(res[pos]).float().cpu()

    def digest(logits):
        probs = logits.softmax(-1)
        tp, ti = probs.topk(topk)
        out = {"top1": wrapper.tokenizer.decode([int(ti[0])]),
               "top1_prob": round(float(tp[0]), 5),
               "topk": [(wrapper.tokenizer.decode([int(i)]), round(float(p), 5))
                        for p, i in zip(tp, ti)]}
        if watch_id is not None:
            out["watch_prob"] = round(float(probs[watch_id]), 6)
            out["watch_rank"] = int((logits > logits[watch_id]).sum()) + 1
        return out

    model_out = digest(unembed_last(acts[final]))
    trace = {}
    if lens is not None:
        for l in watch_layers:
            if l not in lens.source_layers:
                continue
            trace[l] = digest(wrapper.unembed(lens.transport(acts[l][pos], l)).float().cpu())
    return {"model": model_out, "lens_trace": trace}


@torch.no_grad()
def generate(loaded, tok, prompt, n, device, writer_fn=None, writer_layer=None, blocks=None, once=False):
    ids = tok(prompt, return_tensors="pt").input_ids.to(device)
    handle = make_writer(blocks, writer_layer, writer_fn, once=once) if writer_fn else None
    try:
        out = loaded.generate(ids, max_new_tokens=n, do_sample=False, use_cache=True)
    finally:
        if handle is not None:
            handle.remove()
    return tok.decode(out[0], skip_special_tokens=True)


# ------------------------------------------------------------------------ vecs

def vec_from_token(loaded, tok, text: str) -> torch.Tensor:
    tid = tok.encode(text, add_special_tokens=False)[-1]
    emb = loaded.get_input_embeddings().weight[tid].detach().float()
    return emb


def vec_from_diff(wrapper, blocks, a: str, b: str, layer: int, pos: int) -> torch.Tensor:
    return capture(wrapper, blocks, a, layer, pos) - capture(wrapper, blocks, b, layer, pos)


# ------------------------------------------------------------------------- main

def parse_sweep(spec: str):
    import re
    ml = re.search(r"layers=([\d:]+)", spec)
    ma = re.search(r"alphas=([\d.,\s]+)", spec)
    if not ml or not ma:
        raise SystemExit('--sweep needs layers=... and alphas=..., e.g. "layers=0:26:2,alphas=1,2,4,8"')
    parts = [int(x) for x in ml.group(1).split(":")]
    layer_list = list(range(parts[0], parts[1] + 1, parts[2])) if len(parts) == 3 else parts
    alphas = [float(x) for x in re.split(r"[, ]+", ma.group(1).strip()) if x]
    return layer_list, alphas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="0.6B", choices=list(MODELS.keys()))
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--lens", default=None, help="lens .pt override")
    ap.add_argument("--no-lens", action="store_true")
    ap.add_argument("--pos", type=int, default=-1)
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--probe", action="store_true", help="clean readout only")
    ap.add_argument("--watch-token", default=None)

    ap.add_argument("--op", default=None, choices=["add", "proj_out", "scale", "swap"])
    ap.add_argument("--layer", type=int, default=None)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--vec-token", default=None)
    ap.add_argument("--vec-diff-a", default=None)
    ap.add_argument("--vec-diff-b", default=None)
    ap.add_argument("--vec-file", default=None)
    ap.add_argument("--swap-from", default=None)
    ap.add_argument("--gen", type=int, default=0)
    ap.add_argument("--once", action="store_true",
                    help="apply the edit only on the first forward (prefill); generate runs free")
    ap.add_argument("--sweep", default=None, help='e.g. "layers=0:26:2,alphas=1,2,4,8"')
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    t0 = time.time()
    loaded, tok, wrapper = load_model(args.model, args.device)
    blocks = wrapper.layers
    lens = None if args.no_lens else load_lens(args.model, args.lens)
    n_layers = wrapper.n_layers
    layer = args.layer if args.layer is not None else (n_layers // 2)
    watch_id = tok.encode(args.watch_token, add_special_tokens=False)[-1] if args.watch_token else None
    watch_layers = lens.source_layers if lens else []
    print(f"model={args.model} n_layers={n_layers} d_model={wrapper.d_model} device={args.device}")
    print(f"lens={'loaded (%d layers)' % len(lens.source_layers) if lens else 'none'}  op_layer={layer} pos={args.pos}")

    result = {"model": args.model, "prompt": args.prompt, "op": args.op, "layer": layer,
              "pos": args.pos,

              "device": args.device}

    def show(tag, r):
        m = r["model"]
        head = f"  [{tag}] top1={m['top1']!r} p={m['top1_prob']:.4f}"
        if "watch_rank" in m:
            head += f"  | {args.watch_token!r} rank={m['watch_rank']} p={m['watch_prob']:.5f}"
        print(head)
        print("      top%d: %s" % (args.topk, ", ".join(f"{t!r} {p:.4f}" for t, p in m["topk"])))
        if r["lens_trace"]:
            first = None
            for l, d in r["lens_trace"].items():
                if "watch_rank" in d and d["watch_rank"] <= 5 and first is None:
                    first = l
            if first is not None and args.watch_token:
                print(f"      lens: {args.watch_token!r} enters top-5 from layer {first} (upgrade readout)")
            l0 = sorted(r["lens_trace"])[len(r["lens_trace"]) // 2]
            d0 = r["lens_trace"][l0]
            print(f"      lens@L{l0}: top1={d0['top1']!r} p={d0['top1_prob']:.4f}")

    # ------------------------------------------------------------- sweep mode
    if args.sweep:
        layer_list, alphas = parse_sweep(args.sweep)
        rows = []
        print(f"\nSWEEP: {len(layer_list)} layers x {len(alphas)} alphas (op=add, vec per-layer diff)")
        for L in layer_list:
            vec = vec_from_diff(wrapper, blocks, args.vec_diff_a, args.vec_diff_b, L, args.pos)
            for a in alphas:
                r = readout(wrapper, blocks, lens, args.prompt,
                            writer_fn=op_add(vec, a, args.pos), writer_layer=L,
                            watch_layers=[L], pos=args.pos, watch_id=watch_id, topk=3)
                m = r["model"]
                rows.append({"layer": L, "alpha": a, "top1": m["top1"], "p": m["top1_prob"],
                             "watch_rank": m.get("watch_rank")})
                print(f"  L{L:02d} a={a:<4} -> top1={m['top1']!r} p={m['top1_prob']:.4f}"
                      + (f" rank={m.get('watch_rank')}" if watch_id is not None else ""))
        result["sweep"] = rows
        result["sweep_sec"] = round(time.time() - t0, 1)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=1)
            print(f"saved -> {args.report}")
        return

    # ------------------------------------------------------- probe / op modes
    base = readout(wrapper, blocks, lens, args.prompt, watch_layers=watch_layers,
                   pos=args.pos, watch_id=watch_id, topk=args.topk)
    result["clean"] = base
    print("\nCLEAN (no edit):")
    show("clean", base)
    gen_clean = None
    if args.gen:
        gen_clean = generate(loaded, tok, args.prompt, args.gen, args.device)
        result["gen_clean"] = gen_clean
        print(f"  [gen] {gen_clean!r}")

    if args.probe or args.op is None:
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=1)
            print(f"saved -> {args.report}")
        print(f"done in {time.time() - t0:.1f}s")
        return

    # build the op
    if args.op == "swap":
        if not args.swap_from:
            raise SystemExit("--op swap needs --swap-from")
        src = capture(wrapper, blocks, args.swap_from, layer, args.pos)
        fn = op_swap(src, args.pos)
        vec_desc = f"swap<- {args.swap_from!r} @L{layer}"
    elif args.vec_token:
        fn_map = {"add": lambda v: op_add(v, args.alpha, args.pos),
                  "proj_out": lambda v: op_proj_out(v, args.pos),
                  "scale": lambda v: op_scale(v, args.scale, args.pos)}
        fn = fn_map[args.op](vec_from_token(loaded, tok, args.vec_token))
        vec_desc = f"token {args.vec_token!r}"
    elif args.vec_file:
        v = torch.load(args.vec_file, map_location="cpu").float().flatten()
        fn_map = {"add": lambda vv: op_add(vv, args.alpha, args.pos),
                  "proj_out": lambda vv: op_proj_out(vv, args.pos),
                  "scale": lambda vv: op_scale(vv, args.scale, args.pos)}
        fn = fn_map[args.op](v)
        vec_desc = f"file {args.vec_file}"
    elif args.vec_diff_a and args.vec_diff_b:
        v = vec_from_diff(wrapper, blocks, args.vec_diff_a, args.vec_diff_b, layer, args.pos)
        fn_map = {"add": lambda vv: op_add(vv, args.alpha, args.pos),
                  "proj_out": lambda vv: op_proj_out(vv, args.pos),
                  "scale": lambda vv: op_scale(vv, args.scale, args.pos)}
        fn = fn_map[args.op](v)
        vec_desc = f"diff({args.vec_diff_a!r} - {args.vec_diff_b!r})"
    else:
        raise SystemExit("need a vector source: --vec-token / --vec-diff-a+b / --vec-file / --swap-from")

    edited = readout(wrapper, blocks, lens, args.prompt, writer_fn=fn, writer_layer=layer,
                     watch_layers=watch_layers, pos=args.pos, watch_id=watch_id, topk=args.topk)
    result["edit"] = {"op": args.op, "vec": vec_desc, "alpha": args.alpha, "scale": args.scale,
                      "result": edited}
    print(f"\nEDITED ({args.op} @L{layer}, {vec_desc}"
          + (f", alpha={args.alpha}" if args.op == "add" else "")
          + (f", k={args.scale}" if args.op == "scale" else "") + "):")
    show("edit", edited)
    if args.gen:
        gen_edit = generate(loaded, tok, args.prompt, args.gen, args.device, writer_fn=fn,
                            writer_layer=layer, blocks=blocks, once=args.once)
        result["gen_edit"] = gen_edit
        print(f"  [gen] {gen_edit!r}")

    result["sec"] = round(time.time() - t0, 1)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        print(f"saved -> {args.report}")
    print(f"done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
