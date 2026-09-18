# -*- coding: utf-8 -*-
"""Score 2021 prospective test: committed answers vs real answers."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

mine = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_my_answers.json', encoding='utf-8'))
data = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\data__contest8_2021.json', encoding='utf-8'))

# Build answer key
answer_key = {}
for item in data:
    if 'questions' not in item:
        continue
    for qq in item['questions']:
        answer_key[qq['question_id']] = qq['answer']

correct = total = 0
detail = []
for qid, my in mine.items():
    real = answer_key.get(qid, '?')
    ok = my == real
    total += 1
    correct += ok
    detail.append('%s %s->%s %s' % (qid, my, real, 'OK' if ok else 'X'))

lines = ['=== 2021 Prospective Test (40 new questions, never seen before) ===']
lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
lines.append('')
lines.append('Comparison with existing 160-question benchmark: 40.0%')
lines.append('Comparison with Claude Opus 4.6 baseline: 40.0% (2025, 40Q)')
lines.append('Comparison with Tianfu Agent: 50.0% (2025, 40Q)')
lines.append('')
lines += detail
with open(r'E:\ming_li_skill\MingLiSkill\new_bench\score_2021.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Score: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
