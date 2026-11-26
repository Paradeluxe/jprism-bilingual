# -*- coding: utf-8 -*-
"""Enforce one lower-order term per sentence in the generator."""
import io

p = 'manuscript/_apply_threeway_template.py'
s = io.open(p, encoding='utf-8').read()
start = s.index('def lower_para(')
end = s.index('def simple_sentence(')
new = '''def lower_para(dv, effects):
    s = [stat(dv, e) for e in effects]
    table = 'A12' if dv == 'overlap' else 'A11'
    if dv == 'overlap':
        label = ['the main effect of overlap type', 'the main effect of prompt language',
                 'the main effect of probe family', 'the overlap type by prompt interaction',
                 'the overlap type by probe family interaction',
                 'the prompt by probe family interaction']
        p_sentence = 'All p < .001 except probe family.'
    else:
        label = ['the main effect of lens language', 'the main effect of prompt language',
                 'the main effect of probe family', 'the lens by prompt interaction',
                 'the lens by probe family interaction', 'the prompt by probe family interaction']
        p_sentence = 'All p < .001.'
    opening = ''
    if dv == 'share_zh':
        opening = 'All six lower-order terms were significant in all ten models.'
    elif dv == 'share_ru':
        opening = 'All six lower-order terms were significant in every model.'
    elif dv == 'blackout_pool':
        opening = ('For pool blackout (the share of measured layers on which a lens was dark), '
                   'the first main effect below is lens language.')
    sentences = []
    for i in range(6):
        if dv == 'share_non' and i == 2:
            bad = TAGLABEL.get(s[2]['bad'][0], s[2]['bad'][0]) if s[2]['bad'] else ''
            sentences.append('The main effect of probe family was significant in nine of the ten '
                             'models, %s, with %s the exception (p = .16).'
                             % (s[2]['f'], bad))
        else:
            subj = label[i]
            if dv == 'blackout_pool' and i == 0:
                subj = 'the main effect of lens language'
            sentences.append('The %s was significant, %s.' % (subj, s[i]['f']))
    if dv == 'share_non':
        p_sentence = 'All p < .001 except probe family.'
    body = []
    if opening and dv != 'blackout_pool':
        body.append(opening)
    body.extend(sentences)
    body.append(p_sentence)
    body.append('Table %s reports the complete simple-effect contrasts.' % table)
    return ' '.join(body)


'''
s = s[:start] + new + s[end:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('lower_para rewritten (one term per sentence)')
