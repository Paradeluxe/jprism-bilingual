# -*- coding: utf-8 -*-
"""Fix the just-written lower_para wording."""
import io

p = 'manuscript/_apply_threeway_template.py'
s = io.open(p, encoding='utf-8').read()
start = s.index('def lower_para(')
end = s.index('def simple_sentence(')
new = '''def lower_para(dv, effects):
    s = [stat(dv, e) for e in effects]
    table = 'A12' if dv == 'overlap' else 'A11'
    if dv == 'overlap':
        labels = ['main effect of overlap type', 'main effect of prompt language',
                  'main effect of probe family', 'overlap type by prompt interaction',
                  'overlap type by probe family interaction', 'prompt by probe family interaction']
        p_sentence = 'All p < .001 except probe family.'
    else:
        labels = ['main effect of lens language', 'main effect of prompt language',
                  'main effect of probe family', 'lens by prompt interaction',
                  'lens by probe family interaction', 'prompt by probe family interaction']
        p_sentence = 'All p < .001.'
    if dv == 'share_non':
        p_sentence = 'All p < .001 except probe family.'
    sentences = []
    for i in range(6):
        if dv == 'share_non' and i == 2:
            bad = TAGLABEL.get(s[2]['bad'][0], s[2]['bad'][0]) if s[2]['bad'] else ''
            sentences.append('The main effect of probe family was significant in nine of the ten '
                             'models, %s, with %s the exception (p = .16).'
                             % (s[2]['f'], bad))
        elif dv == 'blackout_pool' and i == 0:
            sentences.append('For pool blackout (the share of measured layers on which a lens '
                             'was dark), the main effect of lens language was significant, %s.'
                             % s[0]['f'])
        else:
            sentences.append('The %s was significant, %s.' % (labels[i], s[i]['f']))
    body = []
    if dv == 'share_zh':
        body.append('All six lower-order terms were significant in all ten models.')
    elif dv == 'share_ru':
        body.append('All six lower-order terms were significant in every model.')
    body.extend(sentences)
    body.append(p_sentence)
    body.append('Table %s reports the complete simple-effect contrasts.' % table)
    return ' '.join(body)


'''
s = s[:start] + new + s[end:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('lower_para corrected')
