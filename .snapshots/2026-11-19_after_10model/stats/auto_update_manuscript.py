# -*- coding: utf-8 -*-
"""Automation: when a new model has complete PROBE300 results, refresh the manuscript numbers.

What it does, in order:
  1. scan  experiment/RESULT/PROBE300  for tags with all 3 lenses x 3 prompts as raw files;
  2. pull missing raw files from the cluster (optional, --pull);
  3. patch the model lists inside every pipeline script from experiment/manuscript_models.json;
  4. rebuild the item-level / overlap / blackout / long datasets;
  5. re-fit the ten-model LMMs (F, Satterthwaite df, post-hoc t);
  6. re-render Figures 1-4 and rewrite Table 2 plus the figure captions in the manuscript;
  7. write  experiment/stats_mixed/results/UPDATE_REPORT.md  with the new numbers and the text
     locations that must be re-typed.

Usage:
  python auto_update_manuscript.py --check          # only report what changed on disk
  python auto_update_manuscript.py --run            # full refresh (no cluster pull)
  python auto_update_manuscript.py --run --pull     # also scp missing raw files from the cluster
  python auto_update_manuscript.py --add qwen3-32b --family Qwen3 --layers 64 --d_model 5120
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATS = os.path.join(HERE, 'stats_mixed')
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import manuscript_models as REG  # noqa: E402

P300 = os.path.join(HERE, 'RESULT', 'PROBE300')
LENS_FILE = {'en': 'wikitext', 'zh': 'zhwiki', 'ru': 'ruwiki'}
PROMPT = ['en', 'zh', 'ru']
PY = sys.executable


def _can(python, module):
    return subprocess.run([python, '-c', 'import ' + module],
                          capture_output=True).returncode == 0


def _pick(candidates, module):
    for c in candidates:
        if c and os.path.isfile(c) and _can(c, module):
            return c
    return sys.executable


STATS_PY = os.environ.get('STATS_PY') or _pick(
    [os.path.join(HERE, '.venv-stats', 'Scripts', 'python.exe'),
     os.path.join(HERE, '.venv', 'Scripts', 'python.exe')], 'rpy2')
DATA_PY = os.environ.get('DATA_PY') or _pick(
    [os.path.join(HERE, '.venv', 'Scripts', 'python.exe'),
     os.path.join(HERE, '.venv-stats', 'Scripts', 'python.exe')], 'pandas')
MANU_PY = os.environ.get('MANUSCRIPT_PY') or _pick(
    [sys.executable,
     os.path.expandvars(r'%USERPROFILE%\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe'),
     'python'], 'docx')

# scripts whose TAGS list follows the registry
TAG_PATCH_FILES = [
    os.path.join(STATS, 'run_star_models.py'),
    os.path.join(STATS, 'run_overlap_lmm.py'),
    os.path.join(STATS, 'run_pool_bo_lmm.py'),
    os.path.join(STATS, 'run_single_bo_lmm.py'),
    os.path.join(STATS, 'add_term_df.py'),
    os.path.join(STATS, 'add_pairwise_t.py'),
    os.path.join(STATS, 'build_core_csv.py'),
    os.path.join(STATS, 'build_blackout_exclusive.py'),
    os.path.join(STATS, 'build_dataset.py'),
    os.path.join(STATS, 'overlap', 'build_overlap.py'),
]


def raw_files(tag):
    out = []
    for lens in LENS_FILE.values():
        for prompt in PROMPT:
            out.append(os.path.join(P300, 'PROBE300_%s_%s_%s_raw.json'
                                    % (tag, lens, prompt)))
    return out


def complete_tags():
    """Tags with every lens x prompt cell present on disk."""
    tags = set()
    for f in glob.glob(os.path.join(P300, 'PROBE300_*_raw.json')):
        base = os.path.basename(f)[len('PROBE300_'):-len('_raw.json')]
        tag = base.rsplit('_', 2)[0]
        tags.add(tag)
    return {t for t in tags if all(os.path.isfile(p) for p in raw_files(t))}


# quantized / non-main variants are never auto-promoted into the manuscript
IGNORE = re.compile(r'-(q\d|fp8|awq|bnb|gptq|q[2345678])')


def check(reg):
    have = {t for t in complete_tags() if not IGNORE.search(t)}
    known = set(REG.tags(reg))
    new = sorted(have - known)
    missing_files = sorted(t for t in known if not all(os.path.isfile(p) for p in raw_files(t)))
    return new, missing_files


def pull(tags):
    ssh_key = os.path.expanduser('~/.ssh/sicc_yc57337_ed25519')
    host = 'yc57337@gpu.sicc.um.edu.mo'
    scp = 'scp'
    ok = True
    for tag in tags:
        pattern = '%s:~/jspace/RESULT/PROBE300/PROBE300_%s_*_raw.json' % (host, tag)
        cmd = [scp, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=20',
               '-i', ssh_key, pattern, P300]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print('pull %-24s %s' % (tag, 'ok' if r.returncode == 0 else r.stderr.strip()[:120]))
        ok = ok and r.returncode == 0
    return ok


def patch_tag_lists(tags):
    """Rewrite every TAGS/CORE_TAGS list from the registry, preserving the script style."""
    block = ("TAGS = [" + ", ".join("'%s'" % t for t in tags[:4]))
    lines = [block]
    for i in range(4, len(tags), 4):
        lines.append("        " + ", ".join("'%s'" % t for t in tags[i:i + 4]) + "]"
                     if i + 4 >= len(tags) else "        " + ", ".join("'%s'" % t for t in tags[i:i + 4]))
    new_list = "['" + "', '".join(tags) + "']"
    pat = re.compile(r"TAGS = \[[^\]]*\]", re.S)
    core = re.compile(r"CORE_TAGS = \[[^\]]*\]", re.S)
    for path in TAG_PATCH_FILES:
        s = open(path, encoding='utf-8').read()
        changed = pat.sub('TAGS = ' + new_list, s)
        changed = core.sub('CORE_TAGS = ' + new_list, changed)
        if changed != s:
            open(path, 'w', encoding='utf-8', newline='\n').write(changed)
            print('patched tags:', os.path.relpath(path, REPO))


def _replace_block(text, marker, new_block):
    """Replace marker = [ ... ] (nested brackets allowed) with new_block."""
    i = text.find(marker)
    if i < 0:
        return text
    j = text.find('[', i)
    depth = 0
    k = j
    while k < len(text):
        if text[k] == '[':
            depth += 1
        elif text[k] == ']':
            depth -= 1
            if depth == 0:
                break
        k += 1
    return text[:i] + new_block + text[k + 1:]


def patch_figure_lists(reg):
    """Rewrite the Gemma/Qwen model lists in the three figure scripts."""
    fams = {}
    for m in reg['models']:
        fams.setdefault(m['family'], []).append(m)
    order = [f for f in reg.get('families', []) if f in fams]
    order += [f for f in fams if f not in order]

    def pair(m):
        return '("%s", "%s")' % (m['tag'], m['label'])

    def fam_block(family, models, indent):
        pad = ' ' * indent
        body = ', '.join(pair(m) for m in models)
        return '%s("%s", [%s]),' % (pad, family, body)

    # family grids: GEMMA = [ ... ], QWEN = [ ... ]
    p = os.path.join(HERE, 'figures', 'make_family_grids.py')
    s = open(p, encoding='utf-8').read()
    gemma = fams.get('Gemma-4', [])
    qwen_fams = [(f, fams[f]) for f in order if f in ('Qwen3', 'Qwen3.5')]
    gemma_src = 'GEMMA = [%s]' % (fam_block('Gemma-4', gemma, 0).rstrip(','),)
    qwen_lines = ['QWEN = [']
    for i, (f, ms) in enumerate(qwen_fams):
        qwen_lines.append('    ' + fam_block(f, ms, 0))
    qwen_lines.append(']')
    s = _replace_block(s, 'GEMMA = [', gemma_src)
    s = _replace_block(s, 'QWEN = [', '\n'.join(qwen_lines))
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('patched family-grid model lists')

    # overlap figure: ROWS = [ ... ]
    p = os.path.join(HERE, 'figures', 'make_readme_figs_svg.py')
    s = open(p, encoding='utf-8').read()
    rows = ['ROWS = [']
    for f in order:
        rows.append('    ' + fam_block(f, fams[f], 0))
    rows.append(']')
    s = _replace_block(s, 'ROWS = [', '\n'.join(rows))
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('patched overlap rows')

    # blackout heatmap: TAGS = [ ... ]
    p = os.path.join(HERE, 'figures', 'make_blackout_heatmap.py')
    s = open(p, encoding='utf-8').read()
    items = ', '.join('("%s", "%s")' % (m['tag'], m['label']) for m in reg['models'])
    s = _replace_block(s, 'TAGS = [', 'TAGS = [%s]' % items)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('patched blackout tags')


def sh(cmd, env=None, cwd=REPO):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True)
    tail = (r.stdout or '').strip().splitlines()[-2:]
    print('  %-46s %s' % (' '.join(cmd[-2:])[:46], 'ok' if r.returncode == 0 else 'FAILED'))
    for line in tail:
        print('     ', line[:150])
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--pull', action='store_true')
    ap.add_argument('--add', default='')
    ap.add_argument('--family', default='')
    ap.add_argument('--label', default='')
    ap.add_argument('--layers', type=int, default=0)
    ap.add_argument('--d-model', type=int, default=0, dest='d_model')
    ap.add_argument('--steps', default='patch,data,stats,figures,manuscript',
                    help='subset of: patch,data,stats,figures,manuscript')
    args = ap.parse_args()

    reg = REG.load()
    if args.add:
        assert args.family and args.layers, '--add needs --family and --layers'
        reg['models'].append(dict(tag=args.add,
                                  label=args.label or args.add.upper(),
                                  family=args.family,
                                  layers=args.layers,
                                  d_model=args.d_model or 0))
        REG.save(reg)
        print('registered', args.add)

    new, missing = check(reg)
    print('registered models :', len(reg['models']))
    print('complete on disk  :', len(complete_tags()))
    if new:
        print('NEW complete tags (not in the manuscript):', ', '.join(new))
    else:
        print('no new complete model on disk')
    if missing:
        print('registered but raw files missing   :', ', '.join(missing))
    if not args.run:
        return
    if missing and args.pull:
        pull(missing)
        new, missing = check(reg)
        if missing:
            print('still missing after pull:', ', '.join(missing))
            return
    if missing:
        print('run with --pull to fetch the missing raw files first')
        return

    steps = [x.strip() for x in args.steps.split(',') if x.strip()]
    tags = REG.tags(reg)
    if 'patch' in steps:
        print('\n[1/5] patch model lists')
        patch_tag_lists(tags)
        patch_figure_lists(reg)

    if 'data' in steps:
        print('\n[2/5] rebuild item-level datasets')
        sh([DATA_PY, '-u', os.path.join(STATS, 'build_item_level.py'), '--tags', ','.join(tags),
            '--out', os.path.join(STATS, 'data', 'item_level_10.parquet')])
        sh([DATA_PY, '-u', os.path.join(STATS, 'build_core_csv.py')])
        sh([DATA_PY, '-u', os.path.join(STATS, 'build_blackout_exclusive.py')])
        sh([DATA_PY, '-u', os.path.join(STATS, 'overlap', 'build_overlap.py')], cwd=os.path.join(STATS, 'overlap'))
        sh([DATA_PY, '-u', os.path.join(STATS, 'build_dataset.py')])

    if 'stats' in steps:
        print('\n[3/5] re-fit the models')
        renv = {'R_HOME': r'C:\Program Files\R\R-4.4.1', 'RPY2_CFFI_MODE': 'ABI',
                'PATH': r'C:\Program Files\R\R-4.4.1\bin\x64;' + os.environ.get('PATH', '')}
        for script in ['run_star_models.py', 'run_overlap_lmm.py', 'run_pool_bo_lmm.py',
                       'run_single_bo_lmm.py', 'add_term_df.py', 'add_pairwise_t.py']:
            sh([STATS_PY, '-u', os.path.join(STATS, script)], env=renv)

    if 'figures' in steps:
        print('\n[4/5] figures')
        fenv = {'FIG_FS': '1.4', 'FIG_SUFFIX': '_print', 'FIG_PH': '1.5',
                'FIG_YTICK_STEP': '0.25', 'FIG_LENS_GAP': '1.5',
                'FIG_BW': '0.6', 'FIG_LENSW': '0.7', 'FIG_MGAP': '0.7'}
        sh([DATA_PY, '-u', os.path.join(HERE, 'figures', 'make_family_grids.py')], env=fenv,
           cwd=os.path.join(HERE))
        oenv = {'OV_FS': '1.45', 'OV_PANW': '0.75', 'OV_MGAP': '1.9',
                'OV_ROW_GAP': '1.8', 'OV_FGAP': '1.2'}
        cache = os.path.join(STATS, 'data', 'overlap_by_layer_3lens_v2.json')
        if os.path.isfile(cache):
            os.remove(cache)
        sh([DATA_PY, '-u', os.path.join(HERE, 'figures', 'make_readme_figs_svg.py')], env=oenv,
           cwd=os.path.join(HERE))
        sh([DATA_PY, '-u', os.path.join(HERE, 'figures', 'make_blackout_heatmap.py')],
           cwd=os.path.join(HERE))

    if 'stats' in steps:
        print('\n[5/5] digest')
        sh([DATA_PY, '-u', os.path.join(STATS, 'results_digest.py')])

    if 'manuscript' in steps:
        print('\n[5/5] manuscript tables, captions, sections and review report')
        sh([MANU_PY, '-u', os.path.join(REPO, 'manuscript', '_sync_table2.py')])
        sh([MANU_PY, '-u', os.path.join(REPO, 'manuscript', '_split_sections_md.py')])
        sh([MANU_PY, '-u', os.path.join(REPO, 'manuscript', '_write_update_report.py')])
        import shutil
        kind = os.path.join(REPO, 'manuscript', 'sections', '04_results.md')
        if os.path.isfile(kind):
            shutil.copyfile(kind, os.path.join(REPO, 'manuscript', 'results_Nov18.md'))
        print('\nreview report:', os.path.join(STATS, 'results', 'UPDATE_REPORT.md'))
        print('statistics digest:', os.path.join(STATS, 'results', 'RESULTS_DIGEST_10MODEL.md'))
        print('re-read the flagged paragraphs and replace any range that moved.')


if __name__ == '__main__':
    main()
