# -*- coding: utf-8 -*-
"""Remove 'cell' wording from Results prose."""
import io
import re

p = 'manuscript/sections/04_results.md'
s = io.open(p, encoding='utf-8').read()

# direct condition phrases
s = s.replace('in all three prompt language cells', 'under all three prompt languages')
s = s.replace('in all three lens language cells', 'for all three lenses')
s = s.replace('in any of the three prompt language cells, and across cells',
              'under any of the three prompt languages, and across the three prompt languages')
s = s.replace('in any of the three lens language cells, and across cells',
              'for any of the three lenses, and across the three lenses')
s = s.replace('in any of the four overlap type cells, and across cells',
              'for any of the four overlap types, and across the four overlap types')
s = re.sub(r'in the (English|Chinese|Russian)-prompt and (English|Chinese|Russian)-prompt cells',
           r'under \1 and \2 prompts', s)
s = re.sub(r'in the (English|Chinese|Russian)-prompt cell', r'under \1 prompts', s)
s = re.sub(r'in the (English|Chinese|Russian)-lens and (English|Chinese|Russian)-lens cells',
           r'under the \1 and \2 lenses', s)
s = re.sub(r'in the (English|Chinese|Russian)-lens cell', r'under the \1 lens', s)
s = s.replace('in the cross-language unordered type and cross-language ordered type cells',
              'for the cross-language unordered and cross-language ordered types')
s = s.replace('in the cross-language unordered type cell', 'for the cross-language unordered type')
s = s.replace('in the cross-language ordered type cell', 'for the cross-language ordered type')
s = s.replace('in the identical-string unordered type and identical-string ordered type cells',
              'for the identical-string unordered and identical-string ordered types')
s = s.replace('in the identical-string unordered type cell', 'for the identical-string unordered type')
s = s.replace('in the identical-string ordered type cell', 'for the identical-string ordered type')

PROMPTS = ['English', 'Chinese', 'Russian']
LENSES = ['English', 'Chinese', 'Russian']
TYPES = ['cross-language unordered', 'cross-language ordered',
         'identical-string unordered', 'identical-string ordered']


def last_names(prev):
    if any(x + '-prompt' in prev for x in PROMPTS) or 'prompts' in prev:
        found = [x for x in PROMPTS if x in prev]
        if found:
            return 'prompt', found
    if any(x + '-lens' in prev for x in LENSES) or 'lenses' in prev or 'lens' in prev:
        found = [x for x in LENSES if x in prev]
        if found:
            return 'lens', found
    found = [x for x in TYPES if x in prev]
    if found:
        return 'type', found
    return None, []


def phrase(kind, names):
    if not names:
        return ''
    joined = (names[0] if len(names) == 1 else
              '%s and %s' % (names[0], names[1]) if len(names) == 2 else
              '%s and %s' % (', '.join(names[:-1]), names[-1]))
    if kind == 'prompt':
        return 'Under %s prompts' % joined
    if kind == 'lens':
        return 'Under the %s lens' % joined if len(names) == 1 else 'Under the %s lenses' % joined
    return 'For the %s type' % joined if len(names) == 1 else 'For the %s types' % joined


# Replace "In the other N cell(s)" by the complement of the cells named in the
# preceding sentence. Work paragraph by paragraph.
paras = s.split('\n\n')
for pi, para in enumerate(paras):
    if 'In the other ' not in para:
        continue
    # split into sentence chunks but retain delimiters
    chunks = re.split(r'(?<=\.)\s+', para)
    for ci, chunk in enumerate(chunks):
        m = re.match(r'In the other (\d+) cells? (.*)$', chunk)
        if not m:
            continue
        kind, names = None, []
        for back in range(ci - 1, max(-1, ci - 4), -1):
            kind, names = last_names(chunks[back])
            if names:
                break
        if not names:
            continue
        pool = {'prompt': PROMPTS, 'lens': LENSES, 'type': TYPES}[kind]
        rest = [x for x in pool if x not in names]
        if not rest:
            continue
        chunks[ci] = phrase(kind, rest) + ' ' + m.group(2)
    paras[pi] = ' '.join(chunks)
s = '\n\n'.join(paras)

io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
left = [ln for ln in s.splitlines() if re.search(r'\bcell(s)?\b', ln)]
print('remaining lines with cell:', len(left))
for ln in left[:5]:
    print(ln[:200])
