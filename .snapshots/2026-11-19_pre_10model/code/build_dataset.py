#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_dataset.py -- analysis-ready long dataset for the PROBE300 3x3 mixed-model analysis.

WHAT THIS DOES
--------------
Walks the item-level raw measurement files written by
``experiment/share/measure_probe300.py``

    PROBE300_<tag>_<lens>_<promptlang>_raw.json

and emits, for every measured layer of every (model tag, lens, prompt language, item):

  * the language composition of the stored top-100 candidate pool, using the project's own
    classifier from ``experiment/bilingual_align.py`` (``nrm`` / ``_is_language`` / ``_lang``);
  * the project blackout flag;
  * hit@10 and the stored j_rank;
  * depth bookkeeping (``n_layers_total``, ``rel_depth``).

Three files are written under ``--out-dir`` (default: this script's directory):

    data/long.parquet    one row per tag x lens x prompt lang x item x layer
    data/cells.parquet   tidy descriptive aggregate per tag x lens x prompt lang x layer
    validation_report.json  machine-readable validation evidence quoted in DATASET.md

CSV.GZ fallback: if neither pyarrow nor fastparquet is importable, the same tables are written
as ``data/long.csv.gz`` / ``data/cells.csv.gz`` instead (``--format`` forces either).

BAND DEFINITIONS (computed with the project classifier; see bilingual_align._lang)
----------------------------------------------------------------------------------
For each stored candidate ``t`` take ``d = nrm(t)`` (strip + strip BPE marks + casefold):

    band_en         _is_language(d) and _lang(d) == "en"
    band_zh         _is_language(d) and _lang(d) == "zh"
    band_ru         _is_language(d) and _lang(d) == "ru"
    band_x          _is_language(d) and _lang(d) == "x"
                    (hub-marked foreign-Latin words, e.g. parigi/parís)
    band_n_letters  _is_language(d) and _lang(d) == "n"
                    (letter-bearing tokens in other scripts: kana, Arabic, Greek, ...)
    band_non        not _is_language(d)  (digits, punctuation, empty after nrm)
    band_other      band_x + band_n_letters   (the "other letters" band of the task spec)

band_x and band_n_letters are kept as separate columns because measurement hosts differ in
whether the bilingual hub table (which creates the "x" class) was available; band_other is
the analysis-facing sum and is always reported.  Each band column is a count in 0..100 and
the six raw class counts sum to ``pool_size`` (100 in all core measurements).
``pool_non_lang_share`` is ``band_non / pool_size``.

BLACKOUT (project definition, see the manuscript sec. 3.3 / fig. 3 caption reconciliation)
------------------------------------------------------------------------------------------
    blackout = 1  iff  no candidate among the first 10 slots carries a letter
                  and  band_non / pool_size >= 0.50
    blackout = 0  otherwise (an empty pool is never a blackout)

PROVENANCE COLUMNS
------------------
``version``, ``lens_storage``, ``lens_recipe``, ``lens_family`` are copied verbatim from
the raw file's ``meta`` block (None when the measuring host did not record them) and
``raw_file`` is the source basename.  The qwen3-0.6b cells are a local float32 refit and
carry a per-lens recipe hash; the other core tags are legacy measurements whose meta has no
storage/recipe fields.  Downstream analysis can therefore select or exclude refit cells.

VALIDATION (written to validation_report.json and printed at the end)
---------------------------------------------------------------------
1. every pool sums to 100; ``band_non`` equals ``round(non_lang * 100)`` from the raw file;
2. per-cell compose percentages recomputed from the pools are compared with the matching
   ``compose`` row of PROBE300_<tag>_summary.json.  Because some hosts wrote the summary
   without the hub table, the comparison folds the foreign-Latin class into en:
   ours(en+x) vs summary(en+x), ours(n_letters) vs summary(n), zh/ru/non unchanged.
   Deviation must stay below 0.05 pp; a row is only "comparable" when its pool_cells,
   n_cells, source_raw and provenance markers agree with the raw cell that was rebuilt;
3. item counts / layer counts per cell and across the nine cells of a tag;
4. row counts against tag x 9 cells x items x layers.

INPUTS / OUTPUTS
----------------
Raw cells are ~300 items x 12-24 measured layers x 100 stored candidates (~5 MB each); the
script streams one file at a time and keeps only compact tuples, so memory stays moderate.

tag family: ``gemma4-*`` -> gemma4, ``qwen3.5-*`` -> qwen3.5, ``qwen3-*`` -> qwen3.
lens language: wikitext -> en, zhwiki -> zh, ruwiki -> ru.
``n_layers_total`` = number of measured layers recorded per item (identical across the nine
cells of a tag); ``rel_depth = layer / max(measured layer)`` so the deepest measured layer is
1.0.  The model's true layer count is not recorded in the raw files and is not inferred.

USAGE
-----
    python build_dataset.py                                     # core 9 tags, parquet
    python build_dataset.py --tags all                          # everything in RESULT/PROBE300
    python build_dataset.py --tags qwen3-0.6b,qwen3-4b          # explicit subset
    python build_dataset.py --format csv.gz                     # portable fallback

The build is idempotent: re-running overwrites the outputs from whatever raw files exist.
Raw files with a pool whose length is not 100 are still emitted (``pool_size`` column records
it) and are reported by validation instead of being silently dropped.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT = os.path.dirname(HERE)
DEFAULT_P300 = os.path.join(EXPERIMENT, "RESULT", "PROBE300")

# --------------------------------------------------------------------------------------
# Project classifier.  Pure stdlib; imported from the experiment root so the band
# definitions can never drift from the measurement code.
# --------------------------------------------------------------------------------------
if EXPERIMENT not in sys.path:
    sys.path.insert(0, EXPERIMENT)
import bilingual_align as ALIGN  # noqa: E402

# --------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------
LENS_ORDER = ["wikitext", "zhwiki", "ruwiki"]
LENS_LANG = {"wikitext": "en", "zhwiki": "zh", "ruwiki": "ru"}
LANG_ORDER = ["en", "zh", "ru"]

# Token classes returned by ALIGN._lang for letter-bearing tokens, plus "non" for tokens
# without any Unicode letter.  "x" is the hub-marked foreign-Latin class of _lang; it is
# *separate* from "n_letters" (letter-bearing tokens in other scripts: kana, Arabic, Greek...)
# even though _lang calls both of them "n"/"x" and compose_share folds them into one bucket.
CLASSES = ["en", "zh", "ru", "x", "n_letters", "non"]
CLASS_IDX = {c: i for i, c in enumerate(CLASSES)}
NON_CLASS = CLASS_IDX["non"]

# Comparison frame for the per-tag summary compose rows: hub-foreign-Latin ("x") folded
# into en, "n_letters" compared against the summary's "n" key.
CORR_BANDS = ["en", "zh", "ru", "n", "non"]

# The 9 core models of the 3x3 (prompt language x lens language) mixed-model design.
CORE_TAGS = [
    "qwen3-0.6b",
    "qwen3-1.7b-bnb4",
    "qwen3-4b",
    "qwen3-14b",
    "qwen3.5-0.8b",
    "qwen3.5-2b",
    "gemma4-e2b",
    "gemma4-e4b",
    "gemma4-12b",
]

RAW_RE = re.compile(
    r"^PROBE300_(?P<tag>.+)_(?P<lens>wikitext|zhwiki|ruwiki)_(?P<lang>en|zh|ru)_raw\.json$"
)

RAW_COLUMNS = [
    # layout of the tuple yielded by read_cell(); band_other is derived afterwards
    "tag", "model_key", "family", "lens_lang", "prompt_lang",
    "item_type", "item_idx", "item_key", "layer",
    "band_en", "band_zh", "band_ru", "band_x", "band_n_letters", "band_non",
    "j_rank", "hit10", "blackout", "pool_non_lang_share", "pool_size",
    "version", "lens_storage", "lens_recipe", "lens_family", "raw_file",
]
LONG_COLUMNS = [
    "tag", "model_key", "family", "lens_lang", "prompt_lang",
    "item_type", "item_idx", "item_key",
    "layer", "n_layers_total", "rel_depth",
    "band_en", "band_zh", "band_ru", "band_other", "band_x", "band_n_letters", "band_non",
    "j_rank", "hit10", "blackout", "pool_non_lang_share", "pool_size",
    # lens / measurement provenance, copied from the raw file's meta block
    "version", "lens_storage", "lens_recipe", "lens_family", "raw_file",
]
INT_COLUMNS = ["item_idx", "layer", "n_layers_total", "band_en", "band_zh", "band_ru",
               "band_other", "band_x", "band_n_letters", "band_non",
               "hit10", "blackout", "pool_size"]
PROV_FIELDS = ("lens_storage", "lens_recipe", "lens_family")


# --------------------------------------------------------------------------------------
# Token -> band code, memoised globally (the pool vocabulary is tiny relative to the cells)
# --------------------------------------------------------------------------------------
_BAND_CACHE: dict[str, int] = {}


def class_code(tok: str) -> int:
    """Class code (0..5) of one stored candidate string, using the project classifier.

    0=en, 1=zh, 2=ru, 3=x (hub-marked foreign Latin), 4=n_letters (letters in another
    script), 5=non (no Unicode letter at all, incl. empty after nrm).
    """
    code = _BAND_CACHE.get(tok)
    if code is not None:
        return code
    d = ALIGN.nrm(tok)
    if not ALIGN._is_language(d):
        code = CLASS_IDX["non"]
    else:
        lang = ALIGN._lang(d)
        if lang in ("en", "zh", "ru"):
            code = CLASS_IDX[lang]
        elif lang == "x":
            code = CLASS_IDX["x"]
        else:                      # _lang() == "n" but the token does carry letters
            code = CLASS_IDX["n_letters"]
    _BAND_CACHE[tok] = code
    return code


def family_of(tag: str) -> str:
    if tag.startswith("gemma4"):
        return "gemma4"
    if tag.startswith("qwen3.5"):
        return "qwen3.5"
    if tag.startswith("qwen3"):
        return "qwen3"
    return "other"


def resolve_tags(spec: str, available: list[str]) -> tuple[list[str], list[str]]:
    """Return (tags_to_build, tags_requested_but_absent)."""
    raw = [s.strip() for s in spec.split(",") if s.strip()]
    if len(raw) == 1 and raw[0].lower() == "all":
        return sorted(available), []
    if len(raw) == 1 and raw[0].lower() == "core":
        raw = list(CORE_TAGS)
    avail = set(available)
    return [t for t in raw if t in avail], [t for t in raw if t not in avail]


# --------------------------------------------------------------------------------------
# Parsing one raw cell
# --------------------------------------------------------------------------------------
def read_cell(path: str) -> tuple[list[tuple], dict]:
    """Parse one PROBE300_*_raw.json file.

    Returns (rows, info): compact tuples in RAW_COLUMNS order (band_other and the two depth
    columns are derived from the whole file set later) plus per-file validation evidence.
    """
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    meta = doc.get("meta") or {}
    results = doc.get("results") or []

    m = RAW_RE.match(os.path.basename(path))
    f_tag, f_lens, f_lang = m.group("tag"), m.group("lens"), m.group("lang")
    tag = meta.get("tag") or f_tag
    lens = meta.get("lens") or f_lens
    prompt_lang = meta.get("lang") or f_lang
    lens_lang = LENS_LANG.get(lens)
    if lens_lang is None:
        raise ValueError("%s: unknown lens %r" % (path, lens))
    family = family_of(tag)
    model_key = meta.get("model")

    info = dict(
        path=path, tag=tag, model_key=model_key, family=family, lens=lens,
        lens_lang=lens_lang, prompt_lang=prompt_lang,
        filename_mismatch=(tag, lens, prompt_lang) != (f_tag, f_lens, f_lang),
        n_items=len(results), item_keys=set(), item_layer_counts=[],
        layer_values=set(), n_rows=0, n_pools=0,
        class_counts=[0, 0, 0, 0, 0, 0],
        # provenance copied verbatim from meta; absent fields are kept as None, never fatal
        meta_compose=meta.get("compose"), meta_pool_cells=meta.get("pool_cells"),
        meta_n_cells=meta.get("n_cells"), version=meta.get("version"),
        lens_storage=meta.get("lens_storage"), lens_recipe=meta.get("lens_recipe"),
        lens_family=meta.get("lens_family"), raw_file=os.path.basename(path),
        pool_size_bad=0, nonlang_mismatch=0, nonlang_missing=0, nonlang_total=0,
        examples=[],
    )

    rows: list[tuple] = []
    base = (tag, model_key, family, lens_lang, prompt_lang)
    prov = (info["version"], info["lens_storage"], info["lens_recipe"],
            info["lens_family"], info["raw_file"])
    for res in results:
        itype = res.get("type")
        iidx = res.get("idx")
        ikey = res.get("key") or "%s#%s" % (itype, iidx)
        info["item_keys"].add(ikey)
        layers = res.get("layers") or []
        info["item_layer_counts"].append(len(layers))
        for lay in layers:
            L = lay.get("L")
            info["layer_values"].add(L)
            top = lay.get("j_top100") or []
            n = len(top)
            cnt = [0, 0, 0, 0, 0, 0]           # en, zh, ru, x, n_letters, non
            codes = [class_code(t) for t in top]
            for c in codes:
                cnt[c] += 1
            dark10 = True
            for c in codes[:10]:
                if c != NON_CLASS:
                    dark10 = False
                    break
            share = (cnt[NON_CLASS] / n) if n else float("nan")
            blackout = 1 if (dark10 and n and share >= 0.50) else 0
            jr = lay.get("j_rank")
            hit10 = 1 if (jr is not None and jr <= 10) else 0
            rows.append(
                base + (itype, iidx, ikey, L,
                        cnt[0], cnt[1], cnt[2], cnt[3], cnt[4], cnt[5],
                        jr, hit10, blackout, share, n) + prov
            )
            info["n_rows"] += 1
            if n:
                info["n_pools"] += 1
                for i in range(6):
                    info["class_counts"][i] += cnt[i]
            if n != 100:
                info["pool_size_bad"] += 1
            raw_nl = lay.get("non_lang")
            info["nonlang_total"] += 1
            if raw_nl is None:
                info["nonlang_missing"] += 1
            elif int(round(raw_nl * 100)) != cnt[NON_CLASS]:
                info["nonlang_mismatch"] += 1
                if len(info["examples"]) < 5:
                    info["examples"].append(dict(
                        item=ikey, layer=L, raw_non_lang=raw_nl,
                        band_non=cnt[NON_CLASS], n=n))
    return rows, info


# --------------------------------------------------------------------------------------
# compose comparison helpers
# --------------------------------------------------------------------------------------
def our_compose_pct(class_counts, n_pools) -> dict[str, float] | None:
    """compose_share() in percent over all pools of one cell, with x kept separate.

    Keys are CLASSES: en, zh, ru, x, n_letters, non.
    """
    if not n_pools:
        return None
    den = n_pools * 100.0
    return {c: 100.0 * class_counts[i] / den for i, c in enumerate(CLASSES)}


def summary_compose_pct(row) -> tuple[dict[str, float] | None, list[str]]:
    """Raw class shares of a summary row's compose dict, in percent (CLASSES keys).

    Summary compose uses {en, zh, ru, x, n, non}.  Hosts that measured without the hub
    table wrote no "x" key at all and folded foreign-Latin tokens into "en"; absent keys
    are therefore read as 0.0 and the folding is undone by ``corrected_compose``.
    """
    comp = row.get("compose")
    if not isinstance(comp, dict):
        return None, []
    out = {c: 0.0 for c in CLASSES}
    unknown = []
    for k, v in comp.items():
        if k in ("en", "zh", "ru", "x"):
            out[k] += float(v)
        elif k == "n":
            out["n_letters"] += float(v)
        elif k == "non":
            out["non"] += float(v)
        else:
            unknown.append(str(k))
    return out, unknown


def corrected_compose(raw_by_class: dict[str, float]) -> dict[str, float]:
    """Comparison frame that folds the hub-foreign-Latin class into en.

        en   = en + x        (the "x" tokens are Latin script; old hosts called them en)
        n    = n_letters     (letter-bearing tokens in other scripts)
        zh, ru, non unchanged
    """
    return dict(
        en=raw_by_class["en"] + raw_by_class["x"],
        zh=raw_by_class["zh"],
        ru=raw_by_class["ru"],
        n=raw_by_class["n_letters"],
        non=raw_by_class["non"],
    )


def load_summary_rows(p300_dir: str, tag: str) -> dict[tuple, dict]:
    path = os.path.join(p300_dir, "PROBE300_%s_summary.json" % tag)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    out = {}
    for r in rows:
        out[(r.get("lens"), r.get("lang"))] = r
    return out


# --------------------------------------------------------------------------------------
# Main build
# --------------------------------------------------------------------------------------
def build(p300_dir: str, tags_spec: str, limit: int):
    all_raw = {}
    for path in sorted(glob.glob(os.path.join(p300_dir, "*_raw.json"))):
        m = RAW_RE.match(os.path.basename(path))
        if not m:
            continue
        all_raw.setdefault(m.group("tag"), []).append(path)

    build_tags, absent_tags = resolve_tags(tags_spec, sorted(all_raw))
    if limit:
        build_tags = build_tags[:limit] if len(build_tags) > limit else build_tags
    if not build_tags:
        raise SystemExit("no raw files found for tags %r under %s" % (tags_spec, p300_dir))

    t0 = time.time()
    all_rows: list[tuple] = []
    infos: dict[tuple, dict] = {}          # (tag, lens_lang, prompt_lang) -> info
    cell_rows = collections.Counter()      # (tag, lens_lang, prompt_lang) -> n rows
    cell_classes = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    cell_pools = collections.Counter()
    cell_meta = collections.defaultdict(list)   # (tag, cell) -> [(file meta compose, n_pools)]
    duplicates: list[str] = []
    errors: list[dict] = []

    for tag in build_tags:
        paths = sorted(all_raw.get(tag, []))
        for path in paths:
            name = os.path.basename(path)
            try:
                rows, info = read_cell(path)
            except Exception as exc:                      # malformed cell: report, keep going
                errors.append(dict(file=name, error="%s: %s" % (type(exc).__name__, exc)))
                print("  !! %s: %s" % (name, exc), file=sys.stderr)
                continue
            key = (tag, info["lens_lang"], info["prompt_lang"])
            if key in infos:
                duplicates.append(name)
                print("  !! duplicate cell %s: %s" % (key, name), file=sys.stderr)
                continue
            infos[key] = info
            all_rows.extend(rows)
            cell_rows[key] += len(rows)
            for i in range(6):
                cell_classes[key][i] += info["class_counts"][i]
            cell_pools[key] += info["n_pools"]
            cell_meta[key].append((info["meta_compose"], info["meta_pool_cells"]))
            print("  parsed %-52s items=%-3d layers=%-2d rows=%-5d %.1fs"
                  % (name, info["n_items"], len(info["layer_values"]), info["n_rows"],
                     time.time() - t0), file=sys.stderr)

    if not all_rows:
        raise SystemExit("no rows parsed")
    df = pd.DataFrame.from_records(all_rows)
    df.columns = RAW_COLUMNS

    # ---- per-tag depth bookkeeping ---------------------------------------------------
    tag_layer_values: dict[str, set] = collections.defaultdict(set)
    tag_layer_counts: dict[str, int] = {}
    for (tag, _lens_lang, _prompt_lang), info in infos.items():
        tag_layer_values[tag] |= info["layer_values"]
        tag_layer_counts[tag] = max(tag_layer_counts.get(tag, 0),
                                    max(info["item_layer_counts"] or [0]))
    tag_max_layer = {t: max(v) for t, v in tag_layer_values.items()}
    df["n_layers_total"] = df["tag"].map(tag_layer_counts)
    df["rel_depth"] = df["layer"] / df["tag"].map(tag_max_layer)
    df["band_other"] = df["band_x"] + df["band_n_letters"]   # task-level "other" band

    # deterministic order: core tag order first, then any extra tags alphabetically
    tag_rank = {t: i for i, t in enumerate(CORE_TAGS)}
    df["_tag_rank"] = df["tag"].map(lambda t: tag_rank.get(t, len(CORE_TAGS)))
    df = df.sort_values(
        ["_tag_rank", "tag", "lens_lang", "prompt_lang", "item_type", "item_idx", "layer"],
        kind="mergesort").drop(columns="_tag_rank").reset_index(drop=True)

    for c in INT_COLUMNS:
        df[c] = df[c].astype("int64")
    df["j_rank"] = pd.array([v for v in df["j_rank"].tolist()], dtype="Int64")
    df["pool_non_lang_share"] = df["pool_non_lang_share"].astype("float64")
    for c in ("version",) + PROV_FIELDS + ("raw_file",):
        df[c] = df[c].astype("object")
    df = df[LONG_COLUMNS]

    # ---- cells summary ---------------------------------------------------------------
    pool_size = df["pool_size"].where(df["pool_size"] > 0)
    share_bands = ["en", "zh", "ru", "other", "x", "n_letters", "non"]
    shares = {b: df["band_" + b] / pool_size for b in share_bands}
    work = df[["tag", "model_key", "family", "lens_lang", "prompt_lang",
               "layer", "rel_depth", "item_key", "blackout", "hit10",
               "pool_non_lang_share"]].copy()
    for b in share_bands:
        work["_s_" + b] = shares[b]
    g = work.groupby(["tag", "model_key", "family", "lens_lang", "prompt_lang",
                      "layer", "rel_depth"], sort=False, observed=True)
    cells = g.agg(
        n_rows=("item_key", "size"),
        n_items=("item_key", "nunique"),
        blackout_rate=("blackout", "mean"),
        hit10_rate=("hit10", "mean"),
        mean_pool_non_lang_share=("pool_non_lang_share", "mean"),
    )
    for b in share_bands:
        cells["share_" + b] = g["_s_" + b].mean()
    cells = cells.reset_index().sort_values(
        ["tag", "lens_lang", "prompt_lang", "layer"], kind="mergesort").reset_index(drop=True)
    # one provenance record per (tag, lens, prompt-lang) cell, copied onto every layer row
    prov_by_cell = {(t, ll, pl): (info["version"], info["lens_storage"],
                                  info["lens_recipe"], info["lens_family"])
                    for (t, ll, pl), info in infos.items()}
    for i, col in enumerate(("version", "lens_storage", "lens_recipe", "lens_family")):
        cells[col] = [prov_by_cell[(t, ll, pl)][i]
                      for t, ll, pl in zip(cells["tag"], cells["lens_lang"],
                                           cells["prompt_lang"])]
    cells = cells[["tag", "model_key", "family", "lens_lang", "prompt_lang",
                   "layer", "rel_depth", "n_rows", "n_items",
                   "share_en", "share_zh", "share_ru", "share_other",
                   "share_x", "share_n_letters", "share_non",
                   "blackout_rate", "hit10_rate", "mean_pool_non_lang_share",
                   "version", "lens_storage", "lens_recipe", "lens_family"]]

    # ---- validation ------------------------------------------------------------------
    report = validate(p300_dir, build_tags, infos, cell_rows, cell_classes, cell_pools,
                      cell_meta, all_raw, absent_tags, duplicates, errors, df)
    report["n_rows"] = int(len(df))
    report["n_cells_summary_rows"] = int(len(cells))
    report["elapsed_sec"] = round(time.time() - t0, 1)
    report["band_cache_size"] = len(_BAND_CACHE)

    return df, cells, report


# --------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------
def validate(p300_dir, build_tags, infos, cell_rows, cell_classes, cell_pools, cell_meta,
             all_raw, absent_tags, duplicates, errors, df) -> dict:
    # -- 1) pool-level checks (band sum / raw non_lang agreement) ----------------------
    band_sum = df[["band_en", "band_zh", "band_ru", "band_x", "band_n_letters",
                   "band_non"]].sum(axis=1)
    pool = dict(
        n_rows=int(len(df)),
        n_pool_ne_100=int((df["pool_size"] != 100).sum()),
        n_band_sum_ne_100=int((band_sum != 100).sum()),
        n_band_other_bad=int((df["band_other"] != df["band_x"] + df["band_n_letters"]).sum()),
        n_nonlang_checked=int(sum(i["nonlang_total"] for i in infos.values())),
        n_nonlang_mismatch=int(sum(i["nonlang_mismatch"] for i in infos.values())),
        n_nonlang_missing=int(sum(i["nonlang_missing"] for i in infos.values())),
        examples=[ex for i in infos.values() for ex in i["examples"]][:10],
        n_empty_pools=int((df["pool_size"] == 0).sum()),
    )
    pool["frac_nonlang_match"] = (
        1.0 - pool["n_nonlang_mismatch"] / pool["n_nonlang_checked"]
        if pool["n_nonlang_checked"] else None)

    # -- 2) compose vs summary rows and vs each file's own meta.compose ---------------
    tag_layer_values: dict[str, set] = collections.defaultdict(set)
    tag_layer_count: dict[str, int] = {}
    for (tag, _ll, _pl), info in infos.items():
        tag_layer_values[tag] |= info["layer_values"]
        tag_layer_count[tag] = max(tag_layer_count.get(tag, 0),
                                   max(info["item_layer_counts"] or [0]))

    tags_report: dict[str, dict] = {}
    for tag in build_tags:
        cells_present = sorted({(ll, pl) for (t, ll, pl) in infos if t == tag})
        cells_missing = [(LENS_LANG[lens], lang) for lens in LENS_ORDER for lang in LANG_ORDER
                         if (LENS_LANG[lens], lang) not in set(cells_present)]
        cell_infos = {k: v for k, v in infos.items() if k[0] == tag}
        n_items = {ll + "/" + pl: info["n_items"] for (_, ll, pl), info in cell_infos.items()}
        layer_sets = {ll + "/" + pl: sorted(info["layer_values"])
                      for (_, ll, pl), info in cell_infos.items()}
        n_layers_total = tag_layer_count[tag]
        max_layer = max(tag_layer_values[tag]) if tag_layer_values[tag] else None

        # layer-set / item-set consistency across the tag's cells
        layer_sets_identical = len({tuple(v) for v in layer_sets.values()}) <= 1
        item_sets = {k[1] + "/" + k[2]: info["item_keys"] for k, info in cell_infos.items()}
        canonical_items = max(item_sets.values(), key=len) if item_sets else set()
        item_diffs = {}
        for cell, keys in item_sets.items():
            if keys != canonical_items:
                item_diffs[cell] = dict(
                    missing=sorted(canonical_items - keys)[:10],
                    extra=sorted(keys - canonical_items)[:10],
                    n_missing=len(canonical_items - keys), n_extra=len(keys - canonical_items))
        items_ok = (not item_diffs) and all(v == 300 for v in n_items.values())
        rows_actual = int(sum(cell_rows[(tag, ll, pl)] for (ll, pl) in cells_present))
        rows_expected_present = int(sum(sum(info["item_layer_counts"])
                                        for info in cell_infos.values()))
        rows_expected_full = 9 * 300 * n_layers_total

        # --- compose comparison vs the per-tag summary rows --------------------------
        # Summary compose = {en, zh, ru, x, n, non} percentages.  Two provenance rules:
        #   * hosts without the hub table wrote no "x" key and counted foreign-Latin tokens
        #     as "en", so the comparison folds our x into en on both sides
        #     (ours(en+x) vs summary(en+x), ours(n_letters) vs summary(n);
        #      zh/ru/non unchanged);
        #   * a row is only directly comparable when it aggregated the same raw cell set
        #     (pool_cells / n_cells / source_raw / provenance agree).  Where a local raw
        #     file replaced a legacy measurement the summary may hold other numbers, so the
        #     deviation is classified and reported, never treated as a build failure.
        summary = load_summary_rows(p300_dir, tag)
        compose_cells = []
        for (ll, pl) in cells_present:
            lens_name = {"en": "wikitext", "zh": "zhwiki", "ru": "ruwiki"}[ll]
            info = cell_infos[(tag, ll, pl)]
            n_pools = cell_pools[(tag, ll, pl)]
            n_rows_cell = cell_rows[(tag, ll, pl)]
            ours_raw = our_compose_pct(cell_classes[(tag, ll, pl)], n_pools)
            srow = summary.get((lens_name, pl))
            rec = dict(cell=[ll, pl], lens=lens_name, raw_file=info["raw_file"],
                       ours_pool_cells=n_pools, ours_cells=n_rows_cell,
                       summary_present=srow is not None, summary_has_x=None,
                       summary_pool_cells=None, summary_n_cells=None,
                       summary_source_raw=None, summary_provenance=None,
                       comparable=False, reasons=[], flagged=False)
            if srow is None:
                rec["reasons"] = ["summary row absent"]
                compose_cells.append(rec)
                continue
            sraw, unknown = summary_compose_pct(srow)
            rec["summary_has_x"] = "x" in (srow.get("compose") or {})
            reasons = []
            if unknown:
                reasons.append("unknown compose keys %r" % (unknown,))
            rec["summary_pool_cells"] = srow.get("pool_cells")
            rec["summary_n_cells"] = srow.get("n_cells")
            rec["summary_source_raw"] = srow.get("source_raw")
            rec["summary_provenance"] = {k: srow.get(k) for k in PROV_FIELDS}
            if srow.get("pool_cells") is not None and srow["pool_cells"] != n_pools:
                reasons.append("summary pool_cells %s != ours %s"
                               % (srow["pool_cells"], n_pools))
            if srow.get("n_cells") is not None and srow["n_cells"] != n_rows_cell:
                reasons.append("summary n_cells %s != ours %s"
                               % (srow["n_cells"], n_rows_cell))
            src = srow.get("source_raw")
            if src and src != info["raw_file"]:
                reasons.append("summary source_raw %s != %s" % (src, info["raw_file"]))
            prov_diff = {}
            for k in PROV_FIELDS:
                sp, rp = srow.get(k), info[k]
                if sp is not None and rp is not None and str(sp) != str(rp):
                    prov_diff[k] = [str(sp), str(rp)]
            if prov_diff:
                reasons.append("provenance differs summary->raw: %r" % (prov_diff,))
            if sraw is None or ours_raw is None:
                rec["reasons"] = reasons + ["compose unavailable"]
                compose_cells.append(rec)
                continue
            ours = corrected_compose(ours_raw)
            rsum = corrected_compose(sraw)
            dev = {k: ours[k] - rsum[k] for k in CORR_BANDS}
            max_dev = max(abs(v) for v in dev.values())
            rec.update(
                comparable=not reasons, reasons=reasons,
                ours_classes={c: round(ours_raw[c], 4) for c in CLASSES},
                summary_classes={c: round(sraw[c], 4) for c in CLASSES},
                ours_pct={k: round(ours[k], 4) for k in CORR_BANDS},
                summary_pct={k: round(rsum[k], 4) for k in CORR_BANDS},
                dev_pp={k: round(v, 4) for k, v in dev.items()},
                max_abs_dev_pp=round(max_dev, 6),
                flagged=bool(max_dev >= 0.05),
            )
            compose_cells.append(rec)

        comparable = [c for c in compose_cells if c["comparable"] and "max_abs_dev_pp" in c]
        all_dev = [c["max_abs_dev_pp"] for c in compose_cells if "max_abs_dev_pp" in c]
        comp_dev = [c["max_abs_dev_pp"] for c in comparable]
        sum_flagged = [dict(cell=c["cell"], max_dev_pp=c["max_abs_dev_pp"],
                            comparable=c["comparable"], reasons=c["reasons"])
                       for c in compose_cells if c.get("flagged")]
        not_comparable = [dict(cell=c["cell"], reasons=c["reasons"])
                          for c in compose_cells if not c["comparable"]]
        has_x = [c["summary_has_x"] for c in compose_cells if c["summary_has_x"] is not None]

        # --- compose self-consistency vs every file's own meta.compose ------------------
        # Same folding rule: meta.compose was written by whatever classifier the measuring
        # host shipped, so compare in the folded frame.
        meta_devs, meta_flagged, meta_pool_issues = [], [], []
        for (t, ll, pl), infos_list in cell_meta.items():
            if t != tag:
                continue
            meta = infos_list[0][0]
            meta_pools = infos_list[0][1]
            if not isinstance(meta, dict):
                continue
            mraw, unknown = summary_compose_pct(dict(compose=meta))
            ours_raw = our_compose_pct(cell_classes[(tag, ll, pl)],
                                       cell_pools[(tag, ll, pl)])
            if mraw is None or ours_raw is None:
                continue
            ours = corrected_compose(ours_raw)
            msum = corrected_compose(mraw)
            dev = max(abs(ours[k] - msum[k]) for k in CORR_BANDS)
            meta_devs.append(dev)
            if dev >= 0.05:
                meta_flagged.append(dict(cell=[ll, pl], max_dev_pp=round(dev, 4),
                                         ours={k: round(ours[k], 4) for k in CORR_BANDS},
                                         meta={k: round(msum[k], 4) for k in CORR_BANDS}))
            if meta_pools is not None and meta_pools != cell_pools[(tag, ll, pl)]:
                meta_pool_issues.append(dict(cell=[ll, pl], meta_pool_cells=meta_pools,
                                             ours_pool_cells=cell_pools[(tag, ll, pl)]))

        # --- provenance groups (recipe / storage hash per measured cell) ---------------
        prov_groups = collections.defaultdict(list)
        for (_, ll, pl), info in cell_infos.items():
            prov_groups[(info["version"], info["lens_storage"], info["lens_recipe"],
                         info["lens_family"])].append([ll, pl])
        provenance = [
            dict(version=k[0], lens_storage=k[1], lens_recipe=k[2], lens_family=k[3],
                 cells=sorted(v))
            for k, v in sorted(prov_groups.items(), key=lambda kv: str(kv[0]))
        ]
        has_refit = any(info["lens_recipe"] is not None and
                        not str(info["lens_recipe"]).startswith("legacy:")
                        for info in cell_infos.values())

        tags_report[tag] = dict(
            family=family_of(tag),
            cells_present=sorted([list(c) for c in cells_present]),
            cells_missing=[list(c) for c in cells_missing],
            n_cells=len(cells_present),
            n_items=n_items,
            items_ok=bool(items_ok),
            item_key_diffs=item_diffs,
            layer_sets=layer_sets,
            layer_sets_identical=bool(layer_sets_identical),
            n_layers_total=n_layers_total,
            max_layer=max_layer,
            n_rows=int(rows_actual),
            n_rows_expected_present=int(rows_expected_present),
            n_rows_expected_full=int(rows_expected_full),
            n_rows_match=bool(rows_actual == rows_expected_present),
            provenance=provenance,
            has_refit_provenance=bool(has_refit),
            compose_summary=dict(
                n_cells=len(compose_cells),
                n_comparable=len(comparable),
                n_flagged=len(sum_flagged),
                n_summary_rows_with_x=sum(1 for v in has_x if v),
                n_summary_rows_without_x=sum(1 for v in has_x if not v),
                max_abs_dev_pp_comparable=(None if not comp_dev
                                           else round(max(comp_dev), 6)),
                max_abs_dev_pp_all=(None if not all_dev else round(max(all_dev), 6)),
                flagged=sum_flagged,
                not_comparable=not_comparable,
                cells=compose_cells,
            ),
            compose_meta=dict(
                n_dev_obs=len(meta_devs),
                max_dev_pp=None if not meta_devs else round(max(meta_devs), 6),
                flagged=meta_flagged,
                pool_cell_mismatch=meta_pool_issues,
            ),
        )

    # -- 3) cross-tag item universe ----------------------------------------------------
    tag_items = {}
    for tag in build_tags:
        infos_t = [v for k, v in infos.items() if k[0] == tag]
        if infos_t:
            tag_items[tag] = max((i["item_keys"] for i in infos_t), key=len)
    cross = dict(n_tags=len(tag_items), identical=True, diffs={})
    if len(tag_items) > 1:
        canon = max(tag_items.values(), key=len)
        for tag, keys in tag_items.items():
            if keys != canon:
                cross["identical"] = False
                cross["diffs"][tag] = dict(
                    n_missing=len(canon - keys), n_extra=len(keys - canon),
                    missing=sorted(canon - keys)[:10], extra=sorted(keys - canon)[:10])

    # -- 4) inventory of every raw file on disk (built or not) -------------------------
    inventory = {}
    for tag, paths in sorted(all_raw.items()):
        cells = []
        for p in paths:
            m = RAW_RE.match(os.path.basename(p))
            if m:
                cells.append([LENS_LANG[m.group("lens")], m.group("lang")])
        inventory[tag] = dict(n_raw_files=len(paths), cells=sorted(cells),
                              built=tag in build_tags,
                              core=tag in CORE_TAGS)

    return dict(
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        p300_dir=p300_dir,
        build_tags=build_tags,
        absent_tags=absent_tags,
        duplicates=duplicates,
        errors=errors,
        pool_checks=pool,
        tags=tags_report,
        cross_tag_items=cross,
        inventory=inventory,
        n_band_cache_entries=len(_BAND_CACHE),
    )


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------
def write_tables(df: pd.DataFrame, cells: pd.DataFrame, out_dir: str, fmt: str) -> str:
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    if fmt == "auto":
        try:
            import pyarrow  # noqa: F401
            fmt = "parquet"
        except Exception:
            try:
                import fastparquet  # noqa: F401
                fmt = "parquet"
            except Exception:
                fmt = "csv.gz"
    if fmt == "parquet":
        long_path = os.path.join(data_dir, "long.parquet")
        cells_path = os.path.join(data_dir, "cells.parquet")
        df.to_parquet(long_path, index=False, compression="zstd")
        cells.to_parquet(cells_path, index=False, compression="zstd")
    else:
        long_path = os.path.join(data_dir, "long.csv.gz")
        cells_path = os.path.join(data_dir, "cells.csv.gz")
        df.to_csv(long_path, index=False, compression="gzip")
        cells.to_csv(cells_path, index=False, compression="gzip")
    print("wrote %s (%.1f MB)" % (long_path, os.path.getsize(long_path) / 1e6),
          file=sys.stderr)
    print("wrote %s (%.1f MB)" % (cells_path, os.path.getsize(cells_path) / 1e6),
          file=sys.stderr)
    return fmt


def print_report(report: dict) -> None:
    pc = report["pool_checks"]
    print("\n=== pool checks ===")
    print("rows=%d  pool_size!=100: %d  band_sum!=100: %d  band_other!=x+n_letters: %d"
          "  empty pools: %d"
          % (pc["n_rows"], pc["n_pool_ne_100"], pc["n_band_sum_ne_100"],
             pc["n_band_other_bad"], pc["n_empty_pools"]))
    print("raw non_lang vs band_non: checked=%d  mismatch=%d  missing=%d  match_frac=%s"
          % (pc["n_nonlang_checked"], pc["n_nonlang_mismatch"], pc["n_nonlang_missing"],
             "n/a" if pc["frac_nonlang_match"] is None
             else "%.4f" % pc["frac_nonlang_match"]))

    print("\n=== per-tag ===")
    print("%-18s %-3s %-4s %-3s %-6s %-6s %-5s %-8s %-8s %-4s %-8s %-3s %-7s"
          % ("tag", "cel", "item", "ly", "rows", "exp", "maxL",
             "devCmp", "devAll", "flag", "metaDev", "f32", "sumx(y/n)"))
    for tag, r in report["tags"].items():
        cs = r["compose_summary"]
        print("%-18s %-3d %-4s %-3d %-6d %-6d %-5s %-8s %-8s %-4d %-8s %-3s %-7s"
              % (tag, r["n_cells"],
                 "ok" if r["items_ok"] else "BAD",
                 r["n_layers_total"], r["n_rows"], r["n_rows_expected_present"],
                 r["max_layer"],
                 "%s" % cs["max_abs_dev_pp_comparable"],
                 "%s" % cs["max_abs_dev_pp_all"],
                 cs["n_flagged"],
                 "%s" % r["compose_meta"]["max_dev_pp"],
                 "yes" if r["has_refit_provenance"] else "-",
                 "%d/%d" % (cs["n_summary_rows_with_x"], cs["n_summary_rows_without_x"])))

    print("\n=== provenance (lens_storage / lens_recipe / lens_family) ===")
    for tag, r in report["tags"].items():
        for g in r["provenance"]:
            cells = ",".join("%s/%s" % (a, b) for a, b in g["cells"])
            print("  %-18s storage=%-10s recipe=%-22s family=%-18s cells=%s"
                  % (tag, g["lens_storage"], g["lens_recipe"], g["lens_family"], cells))

    print("\n=== compose deviation table (corrected frame: ours(en+x) vs summary(en+x), pp) ===")
    print("  %-18s %-11s %-9s %-4s %-4s %-6s %-6s %-6s  reasons"
          % ("tag", "cell", "max_dev", "cmp", "flag", "pool", "ncells", "sumx"))
    for tag, r in report["tags"].items():
        for c in r["compose_summary"]["cells"]:
            if "max_abs_dev_pp" not in c:
                print("  %-18s %-11s %-9s %-4s %-4s %-6s %-6s %-6s  %s"
                      % (tag, "/".join(c["cell"]), "-", "no", "-",
                         c["ours_pool_cells"], c["ours_cells"], "-",
                         "; ".join(c["reasons"]) or "summary absent"))
                continue
            print("  %-18s %-11s %-9.5f %-4s %-4s %-6s %-6s %-6s  %s"
                  % (tag, "/".join(c["cell"]), c["max_abs_dev_pp"],
                     "yes" if c["comparable"] else "NO",
                     "FLAG" if c["flagged"] else "-",
                     c["ours_pool_cells"], c["ours_cells"],
                     "yes" if c["summary_has_x"] else "no",
                     "; ".join(c["reasons"])))

    print("\n=== flagged cells (max |deviation| >= 0.05 pp) ===")
    flagged = False
    for tag, r in report["tags"].items():
        for f in r["compose_summary"]["flagged"]:
            flagged = True
            cell = next(c for c in r["compose_summary"]["cells"]
                        if c["cell"] == f["cell"])
            print("  %-18s %-11s max_dev=%.4f pp  comparable=%s  dev_by_band=%s"
                  % (tag, "/".join(f["cell"]), f["max_dev_pp"], f["comparable"],
                     cell.get("dev_pp")))
    if not flagged:
        print("  none")

    print("\n=== coverage / structure ===")
    for tag, r in report["tags"].items():
        if r["cells_missing"]:
            print("  %-18s missing %d cells: %s"
                  % (tag, len(r["cells_missing"]), r["cells_missing"]))
        if not r["items_ok"]:
            print("  %-18s item-count problem: %r" % (tag, r["n_items"]))
        if not r["layer_sets_identical"]:
            print("  %-18s layer sets differ across cells: %r"
                  % (tag, r["layer_sets"]))
        if not r["n_rows_match"]:
            print("  %-18s row count mismatch actual=%d expected=%d"
                  % (tag, r["n_rows"], r["n_rows_expected_present"]))
    if report["absent_tags"]:
        print("  requested but absent on disk: %s" % report["absent_tags"])
    if report["duplicates"]:
        print("  duplicate files: %s" % report["duplicates"])
    if report["errors"]:
        print("  malformed files: %s" % report["errors"])
    print("  cross-tag item universe identical: %s" % report["cross_tag_items"]["identical"])

    inv = report["inventory"]
    core_complete = sum(1 for t, v in inv.items() if v["core"] and v["n_raw_files"] == 9)
    print("  raw files on disk: %d across %d tags; complete core tags: %d/9"
          % (sum(v["n_raw_files"] for v in inv.values()), len(inv), core_complete))
    print("  band cache entries: %d   elapsed: %.1fs"
          % (report["n_band_cache_entries"], report["elapsed_sec"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build the PROBE300 long dataset (bands / blackout / rel_depth) and "
                    "validate it against the per-tag summary compose rows.")
    ap.add_argument("--p300-dir", default=DEFAULT_P300,
                    help="directory holding PROBE300_*_raw.json (default: %(default)s)")
    ap.add_argument("--out-dir", default=HERE,
                    help="output directory (default: this script's directory)")
    ap.add_argument("--tags", default=",".join(CORE_TAGS),
                    help="comma-separated tags, 'core' (default) or 'all'")
    ap.add_argument("--format", choices=["auto", "parquet", "csv.gz"], default="auto")
    ap.add_argument("--limit", type=int, default=0,
                    help="debug: only the first N requested tags (0 = all)")
    args = ap.parse_args(argv)

    print("PROBE300 dir : %s" % args.p300_dir)
    print("out dir      : %s" % args.out_dir)
    df, cells, report = build(args.p300_dir, args.tags, args.limit)

    fmt = write_tables(df, cells, args.out_dir, args.format)
    report["output_format"] = fmt
    report["columns_long"] = LONG_COLUMNS
    report["columns_cells"] = list(cells.columns)
    with open(os.path.join(args.out_dir, "validation_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print_report(report)
    print("\nlong rows: %d   cells rows: %d   format: %s" % (len(df), len(cells), fmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
