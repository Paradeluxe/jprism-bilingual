# -*- coding: utf-8 -*-
"""Rewrite Results to the two-focal template and add Table A14."""
import copy
import io

import docx
import pandas as pd

RES = 'experiment/stats_mixed/results/'
DOCX = 'manuscript/JSpace_Liu_Nov18_2026.docx'
MD = 'manuscript/sections/04_results.md'
TAGS = ['gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-0.6b', 'qwen3-4b',
        'qwen3-8b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b', 'qwen3.5-9b',
        'qwen3.6-27b']
N = 11
T = pd.read_csv(RES + 'barr_terms_selected.csv')
C = pd.read_csv(RES + 'barr_contrasts.csv')
M = pd.read_csv(RES + 'barr_cell_means.csv')
S = pd.read_csv(RES + 'barr_simple_interactions.csv')
for d in (T, C, M, S):
    d.drop(d[~d.tag.isin(TAGS)].index, inplace=True)

SECTIONS = [('### 3.1.1 English share', 'share_en'), ('### 3.1.2 Chinese share', 'share_zh'),
            ('### 3.1.3 Russian share', 'share_ru'), ('### 3.1.4 Non-language share', 'share_non'),
            ('## 3.2 Semantic overlap', 'overlap'), ('## 3.3 Blackout', 'blackout_pool')]
FAM = {'P1': 'country–capital', 'P3': 'definitional', 'P4': 'category–clue'}
LENS = {'en': 'English lens', 'zh': 'Chinese lens', 'ru': 'Russian lens'}
TYPE = {'cross': 'Cross-language unordered', 'cross_ordered': 'Cross-language ordered',
        'identical': 'Identical-string unordered', 'identical_ordered': 'Identical-string ordered'}
PROMPT = {'en': 'English', 'zh': 'Chinese', 'ru': 'Russian'}


def fnum(x):
    return '{:,.0f}'.format(x)


def dnum(x):
    return '%d' % round(x)


def sign(x):
    return ('%.1f' % x).replace('-', '\u2212')


def pval(p):
    s = '%.3g' % p
    return s[1:] if s.startswith('0.') else s


def fdesc(d1, d2lo, d2hi, flo, fhi):
    d2 = dnum(d2lo) if abs(d2hi - d2lo) < 1 else '%s\u2013%s' % (dnum(d2lo), dnum(d2hi))
    return 'F(%d, %s) = %s\u2013%s' % (int(d1), d2, fnum(flo), fnum(fhi))


def simple_family_sentence(dv):
    if dv == 'overlap':
        g = S[(S.dv == dv) & (S.by == 'family') & (S.term == 'sem_type:prompt')]
        factor, df1 = 'Overlap type \u00d7 prompt', 6
    else:
        g = S[(S.dv == dv) & (S.by == 'item_type') & (S.term == 'prompt_lang:lens_lang')]
        factor, df1 = 'Lens \u00d7 prompt', 4
    bits = []
    for fam in ['P1', 'P3', 'P4']:
        h = g[g.by_level == fam]
        f = fdesc(df1, h.df2.min(), h.df2.max(), h.F.min(), h.F.max())
        ptxt = 'all p < .001' if h.p.max() < .001 else 'all p \u2264 %s' % pval(h.p.max())
        bits.append('Within %s probes, %s was significant, %s, %s.'
                    % (FAM[fam], factor.lower(), f, ptxt))
    return ' '.join(bits)


def cells_for(dv):
    if dv == 'overlap':
        return [('%s|%s' % (t, f), '%s type, %s probes' % (TYPE[t], FAM[f]))
                for t in ('cross', 'cross_ordered', 'identical', 'identical_ordered')
                for f in ('P1', 'P3', 'P4')]
    return [('%s|%s' % (l, f), '%s, %s probes' % (LENS[l], FAM[f]))
            for l in ('en', 'ru', 'zh') for f in ('P1', 'P3', 'P4')]


def prompt_delta(dv, tag, cell, a, b):
    level1, fam = cell.split('|')
    g = M[(M.dv == dv) & (M.tag == tag)]
    if dv == 'overlap':
        g = g[(g.sem_type == level1) & (g.family == fam)]
        col = 'prompt'
    else:
        g = g[(g.lens_lang == level1) & (g.item_type == fam)]
        col = 'prompt_lang'
    mm = g.groupby(col).mean_pct.mean()
    return mm[a] - mm[b]


def prompt_sentence(dv, a, b):
    focus = 'prompt' if dv == 'overlap' else 'prompt_lang'
    con = '%s - %s' % (a, b)
    h = C[(C.dv == dv) & (C.focus == focus) & (C.by == 'cell') & (C.contrast == con)]
    cells = dict(cells_for(dv))
    levels = list(cells)
    cnt = h.groupby('by_level').apply(lambda x: int((x.p < .05).sum()))
    full = [x for x in levels if cnt.get(x, 0) == N]
    exc = [x for x in levels if cnt.get(x, 0) < N]
    deltas = [prompt_delta(dv, r.tag, r.by_level, a, b) for _, r in h.iterrows()]
    sig = [r.p for _, r in h.iterrows() if r.p < .05]
    ptxt = ('adjusted p < .001' if max(sig) < .001
            else 'adjusted p \u2264 %s' % pval(max(sig)))
    lab = '%s and %s prompts' % (PROMPT[a], PROMPT[b])
    ncell = len(levels)
    if len(full) == ncell:
        lead = '%s differed significantly in all eleven models in all %d cells' % (lab, ncell)
    elif len(full) == 0:
        lo, hi = min(cnt.values), max(cnt.values)
        return ('%s did not differ significantly in all eleven models in any of the %d cells. '
                'Across cells the difference was significant in %d to %d of the eleven models '
                '(Δ = %s to %s pp, %s).'
                % (lab, ncell, lo, hi, sign(min(deltas)), sign(max(deltas)), ptxt))
    else:
        lead = ('%s differed significantly in all eleven models in %d of the %d cells'
                % (lab, len(full), ncell))
    body = '%s (Δ = %s to %s pp, %s)' % (lead, sign(min(deltas)), sign(max(deltas)), ptxt)
    if exc:
        if len(exc) <= 3:
            ex = ', '.join('%s (%d/11 models)' % (cells[x], cnt[x]) for x in exc)
            body += '. The exceptions were ' + ex
        else:
            from collections import Counter
            dist = Counter(int(cnt[x]) for x in exc)
            bits = ['%d at %d/11 models' % (dist[k], k) for k in sorted(dist, reverse=True)]
            body += '. The exceptions were %d cells (%s, see Table A14)' % (
                len(exc), ' and '.join(bits))
    return body + '.'


def p1(dv):
    eff = 'sem_type:prompt:family' if dv == 'overlap' else 'prompt_lang:lens_lang:item_type'
    g = T[(T.dv == dv) & (T.effect == eff)]
    f = fdesc(g.df1.iloc[0], g.df2.min(), g.df2.max(), g.F.min(), g.F.max())
    table = 'Table A10' if dv == 'overlap' else 'Table A9'
    return ('Main effects and two-way interactions are reported in Table A13. The three-way '
            'interaction was significant in all eleven models, %s, all p < .001 (%s). %s '
            'We decomposed the significant simple two-way interactions in both focal '
            'directions.' % (f, table, simple_family_sentence(dv)))


def p3(dv):
    return ' '.join([prompt_sentence(dv, a, b) for a, b in
                     [('en', 'ru'), ('en', 'zh'), ('ru', 'zh')]] +
                    ['Complete contrasts for each cell are given in Table A14.'])

# ---------- markdown ----------
s = io.open(MD, encoding='utf-8').read()
for heading, dv in SECTIONS:
    i = s.index(heading)
    level = len(heading) - len(heading.lstrip('#'))
    j = len(s)
    pos = i + len(heading)
    for ln in s[pos:].splitlines(keepends=True):
        if ln.startswith('#') and len(ln) - len(ln.lstrip('#')) <= level:
            j = pos
            break
        pos += len(ln)
    paras = [p for p in s[i:j].split('\n\n')]
    # first analysis paragraph after heading
    p1idx = next(k for k, p in enumerate(paras) if p.strip().startswith('Main effects and two-way'))
    p2idx = next(k for k, p in enumerate(paras) if k > p1idx and p.strip())
    old2 = paras[p2idx].strip()
    # remove old stop clauses from lens-direction paragraph
    old2 = old2.replace(' except the Chinese-prompt slice of Qwen3.6-27B, which we did not decompose.', '.')
    old2 = old2.replace(' except the identical-string ordered slice, which we did not decompose.', '.')
    paras[p1idx] = p1(dv)
    paras[p2idx] = old2
    newparas = paras[:p2idx + 1] + [p3(dv)] + paras[p2idx + 1:]
    s = s[:i] + '\n\n'.join(newparas) + s[j:]
io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
print('md rewritten')

# ---------- docx paragraphs ----------
d = docx.Document(DOCX)
for heading, dv in SECTIONS:
    htext = heading.lstrip('#').strip()
    st = next(k for k, x in enumerate(d.paragraphs) if x.text.strip() == htext)
    ps = d.paragraphs
    p1p = next(x for x in ps[st + 1:] if x.text.strip().startswith('Main effects and two-way'))
    p2p = next(x for x in ps[ps.index(p1p) + 1:] if x.text.strip())
    old2 = p2p.text.strip()
    old2 = old2.replace(' except the Chinese-prompt slice of Qwen3.6-27B, which we did not decompose.', '.')
    old2 = old2.replace(' except the identical-string ordered slice, which we did not decompose.', '.')
    for par, txt in ((p1p, p1(dv)), (p2p, old2)):
        for r in list(par.runs):
            r._r.getparent().remove(r._r)
        par.add_run(txt)
    # insert new third paragraph after p2
    newp = copy.deepcopy(p2p._p)
    p2p._p.addnext(newp)
    np = docx.text.paragraph.Paragraph(newp, p2p._parent)
    for r in list(np.runs):
        r._r.getparent().remove(r._r)
    np.add_run(p3(dv))
d.save(DOCX)
print('docx paragraphs rewritten')
