# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
with open(r'E:\ming_li_skill\MingLiSkill\hybrid9_answers.json', encoding='utf-8') as f:
    mine = json.load(f)
correct = total = 0
lines = []
for qid, a in mine.items():
    real = key[qid]['answer']
    ok = a['answer'] == real
    total += 1
    correct += ok
    lines.append('%s %-4s %s->%s %s' % (qid, key[qid].get('category', '?'), a['answer'], real, 'OK' if ok else 'X'))
lines.append('R9: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
# pooled R1-R9: R1-R5 router 45/102 + R6 2/15 + R7 5/15 + R8 5/15 + R9
pc, pn = 45, 102
for af in ['hybrid6_answers.json', 'hybrid7_answers.json', 'hybrid8_answers.json']:
    ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
    for qid in ans:
        pn += 1
lines.append('POOLED R1-R9: %d/%d = %.1f%%' % (pc + correct, pn + total, (pc + correct) / (pn + total) * 100))
with open(r'E:\ming_li_skill\MingLiSkill\hybrid9_score.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('R9: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
print('POOLED R1-R9: %d/%d = %.1f%%' % (pc + correct, pn + total, (pc + correct) / (pn + total) * 100))
