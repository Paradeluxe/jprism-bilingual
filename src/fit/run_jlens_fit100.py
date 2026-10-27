"""Jacobian-lens n100 fit on Qwen3-0.6B - refit with ~100 short prompts."""
from __future__ import annotations

import os
import time
import traceback

os.environ.setdefault("HF_HOME", r"E:\huggingface_cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("TRANSFORMERS_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import logging
import torch
import transformers
import jlens

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

PROJECT = os.path.dirname(os.path.abspath(__file__))
LENS_PATH = os.path.join(PROJECT, "qwen3-0.6b_jacobian_lens_n100.pt")
CKPT_PATH = os.path.join(PROJECT, "fit_ckpt_n100.pt")
OUT_PATH = os.path.join(PROJECT, "experiment_output_n100.txt")
MODEL_NAME = "Qwen/Qwen3-0.6B"
MODEL_ID = r"E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B"

TEST_PROMPTS = [
    "Fact: The currency used in the country shaped like a boot is",
    "The animal that spins webs has how many legs? The number is",
]

# Mid workspace layers (28-layer Qwen3-0.6B)
SOURCE_LAYERS = [8, 12, 14, 16, 20]
MID_LAYER = 14

# ~100 short diverse English sentences (synthesized locally; keep short)
FIT_PROMPTS = [
    "The capital of France is Paris, a city famous for the Eiffel Tower.",
    "Two plus two equals four, and four times five equals twenty.",
    "The sun rises in the east and sets in the west every day.",
    "Water freezes at zero Celsius and boils at one hundred degrees.",
    "A cat is a small domestic animal that often lives with people.",
    "The largest planet in our solar system is Jupiter, a gas giant.",
    "Computers process information using binary digits zero and one.",
    "The Great Wall of China stretches across northern China for miles.",
    "Italy is a country shaped like a boot in southern Europe.",
    "The currency used in many European countries is called the euro.",
    "Spiders spin webs and usually have eight thin legs.",
    "Dogs bark, wag their tails, and often live as loyal pets.",
    "Books are made of paper pages bound together between covers.",
    "Rain falls from clouds when water vapor condenses in the sky.",
    "Mount Everest is the highest mountain peak on planet Earth.",
    "Bread is baked from flour, water, yeast, and a little salt.",
    "The Pacific Ocean is the largest ocean covering Earth surface.",
    "Birds have feathers and most of them can fly through the air.",
    "A triangle has three sides and three corners or angles.",
    "Doctors help sick people get better in hospitals and clinics.",
    "The moon orbits the Earth once every roughly twenty eight days.",
    "Apples are red or green fruits that grow on tall trees.",
    "Trains run on metal tracks and carry passengers between cities.",
    "Fire needs oxygen, fuel, and heat to keep burning brightly.",
    "English is a language spoken in many countries around the world.",
    "Winter is cold and snowy in northern regions of the planet.",
    "Fish live in water and breathe using gills instead of lungs.",
    "A square has four equal sides and four right angles always.",
    "Coffee is a dark drink made from roasted coffee beans.",
    "The Sahara is a vast hot desert located in northern Africa.",
    "Children go to school to learn reading, writing, and math.",
    "Cars use engines and wheels to move people along roads.",
    "Lightning is a sudden flash of electricity during a storm.",
    "Honey is sweet and made by bees from flower nectar.",
    "Australia is both a country and a continent in the south.",
    "Piano keys are black and white and produce musical notes.",
    "Rivers flow from mountains down toward lakes or the sea.",
    "Ice is frozen water that melts when the temperature rises.",
    "The heart pumps blood through the body every single day.",
    "Soccer is a sport played with a round ball and two goals.",
    "Trees produce oxygen and provide shade with green leaves.",
    "Night comes after day when the sun goes below the horizon.",
    "Salt makes food taste better and is found in the ocean.",
    "Airplanes fly high above the clouds carrying many passengers.",
    "The Nile is a long river that runs through Egypt in Africa.",
    "Glass is transparent and often used for windows in houses.",
    "Snowflakes are unique crystals that fall during winter storms.",
    "Elephants are large animals with trunks and big ears.",
    "Maps help people find places and navigate unfamiliar roads.",
    "Time is measured in seconds, minutes, hours, and days.",
    "Milk comes from cows and is used to make cheese and butter.",
    "Volcanoes can erupt with lava, ash, and hot gases suddenly.",
    "The Amazon rainforest is dense with trees and wildlife.",
    "Knives are sharp tools used for cutting food in kitchens.",
    "Stars shine at night because they are distant burning suns.",
    "Bicycles have two wheels and are powered by pedaling legs.",
    "The Atlantic Ocean lies between Europe and the Americas.",
    "Sugar is sweet and comes from sugarcane or sugar beets.",
    "Windows let light into rooms while keeping out cold air.",
    "Frogs start as tadpoles that live in ponds and lakes.",
    "Clocks show the current time with hands or digital numbers.",
    "Gold is a valuable yellow metal used in jewelry and coins.",
    "Wind is moving air that can push sails and turn turbines.",
    "Potatoes grow underground and can be boiled, fried, or baked.",
    "The Earth rotates once per day causing day and night.",
    "Libraries store many books that people can borrow freely.",
    "Whales are large mammals that live in oceans and seas.",
    "Paint covers walls with color and protects them from damage.",
    "Summer is warm and sunny in temperate parts of the world.",
    "Ants live in colonies and work together to gather food.",
    "Bridges connect two sides of a river or deep valley.",
    "Soap cleans dirt from hands when used with warm water.",
    "The North Pole is extremely cold and covered with ice.",
    "Grapes grow on vines and can be made into juice or wine.",
    "Shadows appear when light is blocked by a solid object.",
    "Horses have four legs and people sometimes ride them.",
    "Paper is thin material made from wood pulp for writing.",
    "Thunder is the loud sound that follows a lightning flash.",
    "China has a large population and a very long history.",
    "Oranges are citrus fruits that are usually bright orange.",
    "Keys unlock doors so people can enter locked buildings.",
    "Clouds are made of tiny water droplets floating in air.",
    "Butterflies start as caterpillars before growing wings.",
    "Metals conduct electricity and heat better than wood does.",
    "The equator is an imaginary line around the middle Earth.",
    "Socks keep feet warm and are worn inside shoes daily.",
    "Camels can survive long periods without water in deserts.",
    "Music is organized sound that people enjoy listening to.",
    "Farms grow crops and raise animals for food production.",
    "Ice cream is a frozen sweet dessert many people like.",
    "Japan is an island nation in East Asia with many cities.",
    "Candles burn wax and produce light in dark rooms.",
    "Bees pollinate flowers while collecting nectar for honey.",
    "Mountains are tall landforms that rise above surrounding land.",
    "Shoes protect feet when walking on rough or hard ground.",
    "The human brain controls thoughts, memory, and body movement.",
    "Tomatoes are red fruits often used in salads and sauces.",
    "Boats float on water and can carry people or cargo.",
    "Spring brings warmer weather and blooming flowers outside.",
    "Zebras have black and white stripes on their bodies.",
]


def log(msg: str) -> None:
    print(msg, flush=True)


def show_topk(tok, logits, label: str, rec) -> None:
    topk = logits.topk(5)
    tokens = [tok.decode([int(i)]) for i in topk.indices]
    rec(f"{label}_top5_tokens={tokens}")
    rec(f"{label}_top5_ids={[int(i) for i in topk.indices]}")
    rec(f"{label}_top5_vals={[float(v) for v in topk.values]}")


def apply_one(model, lens, tok, prompt: str, apply_layer: int, rec) -> None:
    rec(f"test_prompt={prompt!r}")
    rec(f"apply_layer={apply_layer} positions=[-2]")
    t2 = time.perf_counter()
    lens_logits, model_logits, input_ids = lens.apply(
        model,
        prompt,
        layers=[apply_layer],
        positions=[-2],
    )
    rec(f"apply_sec={time.perf_counter() - t2:.1f}")
    rec(f"input_ids_len={input_ids.shape[-1]}")
    show_topk(tok, lens_logits[apply_layer][0], "lens", rec)
    show_topk(tok, model_logits[0], "model", rec)


def main() -> None:
    lines: list[str] = []

    def rec(msg: str) -> None:
        log(msg)
        lines.append(msg)

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    rec(f"torch={torch.__version__} cuda={torch.version.cuda} available={torch.cuda.is_available()}")
    rec(f"transformers={transformers.__version__}")
    rec(f"device_count={torch.cuda.device_count()}")
    if torch.cuda.is_available():
        rec(f"gpu={torch.cuda.get_device_name(0)}")
        rec(f"vram_total_gb={torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}")

    dtype = torch.float16
    n_prompts = len(FIT_PROMPTS)
    rec(f"dtype={dtype} model={MODEL_NAME} local={MODEL_ID}")
    rec(f"n_fit_prompts={n_prompts} source_layers={SOURCE_LAYERS}")
    rec(f"dim_batch=4 max_seq_len=64 skip_first=8")

    t0 = time.perf_counter()
    tok = transformers.AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    try:
        hf = transformers.AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            dtype=dtype,
            device_map=None,
            local_files_only=True,
        )
    except TypeError:
        hf = transformers.AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            device_map=None,
            local_files_only=True,
        )
    if torch.cuda.is_available():
        hf = hf.cuda()
    else:
        rec("WARNING: CUDA not available, running on CPU")
    rec(f"load_sec={time.perf_counter() - t0:.1f}")
    if torch.cuda.is_available():
        rec(f"vram_after_load_gb={torch.cuda.memory_allocated() / 1024**3:.2f}")
        rec(f"vram_reserved_gb={torch.cuda.memory_reserved() / 1024**3:.2f}")

    model = jlens.from_hf(hf, tok)
    rec(f"n_layers={model.n_layers} d_model={model.d_model}")

    if os.path.isfile(LENS_PATH):
        rec(f"loading existing lens {LENS_PATH}")
        lens = jlens.JacobianLens.load(LENS_PATH)
        rec(f"lens={lens}")
    else:
        rec(f"fitting lens on {n_prompts} prompts, layers={SOURCE_LAYERS}")
        t1 = time.perf_counter()
        lens = jlens.fit(
            model,
            prompts=FIT_PROMPTS,
            source_layers=SOURCE_LAYERS,
            dim_batch=4,
            max_seq_len=64,
            skip_first=8,
            checkpoint_path=CKPT_PATH,
            checkpoint_every=1,
            resume=True,
        )
        fit_sec = time.perf_counter() - t1
        rec(f"fit_sec={fit_sec:.1f}")
        rec(f"fit_min={fit_sec / 60:.1f}")
        lens.save(LENS_PATH)
        rec(f"saved_lens={LENS_PATH}")
        rec(f"lens={lens}")
        if torch.cuda.is_available():
            rec(f"vram_after_fit_gb={torch.cuda.memory_allocated() / 1024**3:.2f}")
            rec(f"vram_reserved_gb={torch.cuda.memory_reserved() / 1024**3:.2f}")
            rec(f"vram_max_allocated_gb={torch.cuda.max_memory_allocated() / 1024**3:.2f}")

    apply_layer = MID_LAYER if MID_LAYER in lens.source_layers else lens.source_layers[len(lens.source_layers) // 2]
    for i, prompt in enumerate(TEST_PROMPTS):
        rec(f"--- apply test {i + 1}/{len(TEST_PROMPTS)} ---")
        apply_one(model, lens, tok, prompt, apply_layer, rec)
        # Also report neighboring mid layers if present
        for extra in (12, 16):
            if extra in lens.source_layers and extra != apply_layer:
                rec(f"--- extra layer {extra} on test {i + 1} ---")
                apply_one(model, lens, tok, prompt, extra, rec)

    if torch.cuda.is_available():
        rec(f"vram_after_apply_gb={torch.cuda.memory_allocated() / 1024**3:.2f}")
        rec(f"vram_max_allocated_gb={torch.cuda.max_memory_allocated() / 1024**3:.2f}")
        rec(f"vram_reserved_gb={torch.cuda.memory_reserved() / 1024**3:.2f}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    rec(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
