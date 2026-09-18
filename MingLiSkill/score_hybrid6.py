# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
with open(r'E:\ming_li_skill\MingLiSkill\hybrid6_answers.json', encoding='utf-8') as f:
    mine = json.load(f)
correct = total = 0
src_stats = {}
lines = []
for qid, a in mine.items():
    real = key[qid]['answer']
    cat = key[qid].get('category', '?')
    ok = a['answer'] == real
    total += 1
    correct += ok
    src_stats.setdefault(a['source'], [0, 0])
    src_stats[a['source']][0] += ok
    src_stats[a['source']][1] += 1
    lines.append('%s %-4s %-7s %s->%s %s' % (qid, cat, a['source'], a['answer'], real, 'OK' if ok else 'X'))
lines.append('R6: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
for src, s in sorted(src_stats.items()):
    lines.append('  [%s]: %d/%d' % (src, s[0], s[1]))
# pooled hybrid all rounds
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from hybrid_router_v2 import route_answer
pc = pn = 0
for cf, af in [('blind15_charts.json', 'blind15_answers.json'), ('v5blind_charts.json', 'v5blind_answers.json'),
               ('blind30_charts.json', 'blind30_answers.json'), ('hybrid4_charts.json', 'hybrid4_answers.json'),
               ('hybrid5_charts.json', 'hybrid5_answers.json')]:
    charts = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % cf, encoding='utf-8'))}
    ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
    for qid, a in ans.items():
        rs = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        final, _ = route_answer(key[qid].get('category', '?'), a['answer'], rs)
        pn += 1
        pc += (final == key[qid]['answer'])
lines.append('POOLED R1-R6: %d/%d = %.1f%% (prev R1-R5: %d/%d)' % (pc + correct, pn + total, (pc + correct) / (pn + total) * 100, pc, pn))
with open(r'E:\ming_li_skill\MingLiSkill\hybrid6_score.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('R6: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
print('POOLED R1-R6: %d/%d = %.1f%%' % (pc + correct, pn + total, (pc + correct) / (pn + total) * 100))
