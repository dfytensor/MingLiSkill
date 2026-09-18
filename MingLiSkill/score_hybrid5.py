# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
with open(r'E:\ming_li_skill\MingLiSkill\hybrid5_answers.json', encoding='utf-8') as f:
    mine = json.load(f)
correct = total = 0
cat_stats, src_stats = {}, {}
lines = []
for qid, a in mine.items():
    real = key[qid]['answer']
    cat = key[qid].get('category', '?')
    ok = a['answer'] == real
    total += 1
    correct += ok
    cat_stats.setdefault(cat, [0, 0])
    cat_stats[cat][0] += ok
    cat_stats[cat][1] += 1
    src_stats.setdefault(a['source'], [0, 0])
    src_stats[a['source']][0] += ok
    src_stats[a['source']][1] += 1
    lines.append('%s %-6s %-5s %s->%s %s' % (qid, cat, a['source'], a['answer'], real, 'OK' if ok else 'X'))
lines.append('R5 HYBRID: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
for cat, s in sorted(cat_stats.items()):
    lines.append('  %s: %d/%d' % (cat, s[0], s[1]))
for src, s in sorted(src_stats.items()):
    lines.append('  [%s]: %d/%d' % (src, s[0], s[1]))

sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from hybrid_router_v2 import route_answer
pc = pn = 0
pooled_pairs = [('blind15_charts.json', 'blind15_answers.json'),
                ('v5blind_charts.json', 'v5blind_answers.json'),
                ('blind30_charts.json', 'blind30_answers.json'),
                ('hybrid4_charts.json', 'hybrid4_answers.json')]
for cf, af in pooled_pairs:
    charts = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % cf, encoding='utf-8'))}
    ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
    for qid, a in ans.items():
        rs = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        final, _ = route_answer(key[qid].get('category', '?'), a['answer'], rs)
        pn += 1
        pc += (final == key[qid]['answer'])
lines.append('')
lines.append('POOLED HYBRID R1-R5: %d/%d = %.1f%%' % (pc + correct, pn + total, (pc + correct) / (pn + total) * 100))
lines.append('  (R1-R4: %d/%d)' % (pc, pn))
with open(r'E:\ming_li_skill\MingLiSkill\hybrid5_score.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('R5: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
print('POOLED R1-R5: %d/%d = %.1f%%' % (pc + correct, pn + total, (pc + correct) / (pn + total) * 100))
