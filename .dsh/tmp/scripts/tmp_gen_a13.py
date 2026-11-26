import pandas as pd, re

t = pd.read_csv(r"experiment/stats_mixed/results/barr_terms.csv")
old = open(r"manuscript/sections/08_appendix.md", encoding="utf-8").read().split("\n")

# old A13 rows (outcome, term, ...) between header and blank after 42 rows
rows = []
in_tab = False
for l in old[946:990]:
    if l.startswith("| Outcome"):
        in_tab = True; continue
    if in_tab:
        if not l.startswith("|"):
            break
        cells = [c.strip() for c in l.strip("|").split("|")]
        if set(cells[0]) <= set("-: "):
            continue
        rows.append((cells[0], cells[1]))
print("old rows:", len(rows))

outmap = {"English proportion":"share_en","Chinese proportion":"share_zh",
          "Russian proportion":"share_ru","Non-language proportion":"share_non",
          "Pool blackout":"blackout_pool","Semantic overlap":"overlap"}
termmap = {
 ("Lens language"):"lens_lang", ("Prompt language"):"prompt_lang", ("Probe family"):"item_type",
 ("Lens language × Prompt language"):"prompt_lang:lens_lang",
 ("Lens language × Probe family"):"lens_lang:item_type",
 ("Prompt language × Probe family"):"prompt_lang:item_type",
 ("Lens language × Prompt language × Probe family"):"prompt_lang:lens_lang:item_type",
 ("Overlap type"):"sem_type",
 ("Overlap type × Prompt language"):"sem_type:prompt",
 ("Overlap type × probe family"):"sem_type:family",
 ("Overlap type × Probe family"):"sem_type:family",
 ("Overlap type × Prompt language × Probe family"):"sem_type:prompt:family",
}

def fmtp(p):
    if p < .001: return "< .001"
    s = f"{p:.3g}"
    return "≤ " + (s[1:] if s.startswith("0") else s)

out = []
for outcome, term in rows:
    dv = outmap[outcome]
    eff = termmap[term]
    g = t[(t.dv==dv) & (t.effect==eff)]
    if len(g) == 0:
        print("MISSING", outcome, term, dv, eff); continue
    fmin, fmax = g.F.min(), g.F.max()
    df1 = int(g.df1.iloc[0]) if g.df1.nunique()==1 else f"{int(g.df1.min())}-{int(g.df1.max())}"
    d2min, d2max = g.df2.min(), g.df2.max()
    pmax = g.p.max()
    sig = int((g.p < .05).sum())
    N = len(g)
    fstr = f"{fmin:,.0f}–{fmax:,.0f}" if round(fmin)!=round(fmax) else f"{fmin:,.0f}"
    d2str = f"{d2min:,.0f}–{d2max:,.0f}" if round(d2min)!=round(d2max) else f"{d2min:,.0f}"
    mod = f"{sig}/{N}"
    out.append(f"| {outcome} | {term} | {fstr} | {df1} | {d2str} | {fmtp(pmax)} | {mod} |")

print("\n".join(out))
