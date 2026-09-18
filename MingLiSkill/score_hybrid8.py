# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
with open(r'E:\ming_li_skill\MingLiSkill\hybrid8_answers.json', encoding='utf-8') as f:
    mine = json.load(f)
correct = total = 0
lines = []
ss_stats = [0, 0]  # questions where shensha guided the pick
for qid, a in mine.items():
    real = key[qid]['answer']
    ok = a['answer'] == real
    total += 1
    correct += ok
    if '神煞' in a.get('reason', '') or '红鸾' in a.get('reason', '') or '桃花' in a.get('reason', '') or '天喜' in a.get('reason', '') or '华盖' in a.get('reason', '') or '驿马' in a.get('reason', ''):
        ss_stats[0] += ok
        ss_stats[1] += 1
    lines.append('%s %-4s %s->%s %s' % (qid, key[qid].get('category', '?'), a['answer'], real, 'OK' if ok else 'X'))
lines.append('R8: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
lines.append('神煞引导题: %d/%d' % (ss_stats[0], ss_stats[1]))
# pooled R1-R8: R1-R5 via router + R6/R7/R8 committed
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
tot_c, tot_n = pc + correct, pn + total
lines.append('POOLED R1-R8: %d/%d = %.1f%%' % (tot_c, tot_n, tot_c / tot_n * 100))
with open(r'E:\ming_li_skill\MingLiSkill\hybrid8_score.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('R8: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
print('POOLED R1-R8: %d/%d = %.1f%%' % (tot_c, tot_n, tot_c / tot_n * 100))
