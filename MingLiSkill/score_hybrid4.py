# -*- coding: utf-8 -*-
"""Score hybrid round 4 (rules-delegated + agent categories)."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
with open(r'E:\ming_li_skill\MingLiSkill\hybrid4_answers.json', encoding='utf-8') as f:
    mine = json.load(f)

correct = total = 0
cat_stats = {}
src_stats = {}
lines = ['ID         Cat     Src    Mine Real  Result', '-' * 52]
for qid, a in mine.items():
    real = key[qid]['answer']
    cat = key[qid].get('category', '?')
    ok = a['answer'] == real
    total += 1
    correct += ok
    cat_stats.setdefault(cat, {'t': 0, 'c': 0})
    cat_stats[cat]['t'] += 1
    cat_stats[cat]['c'] += ok
    src_stats.setdefault(a['source'], {'t': 0, 'c': 0})
    src_stats[a['source']]['t'] += 1
    src_stats[a['source']]['c'] += ok
    lines.append('%-10s %-7s %-6s %-4s %-4s %s' % (qid, cat, a['source'], a['answer'], real, 'OK' if ok else 'X'))
lines.append('-' * 52)
lines.append('HYBRID total: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
for cat, s in sorted(cat_stats.items()):
    lines.append('  %s: %d/%d' % (cat, s['c'], s['t']))
for src, s in sorted(src_stats.items()):
    lines.append('  [%s]: %d/%d' % (src, s['c'], s['t']))
with open(r'E:\ming_li_skill\MingLiSkill\hybrid4_score.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('pooled: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
