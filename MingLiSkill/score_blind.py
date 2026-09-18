# -*- coding: utf-8 -*-
"""Score a blind test AFTER answers are committed.
Usage: python score_blind.py <answers_json> <label>
"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
ANSWERS_PATH = sys.argv[1]
LABEL = sys.argv[2] if len(sys.argv) > 2 else 'BLIND'

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
with open(ANSWERS_PATH, 'r', encoding='utf-8') as f:
    mine = json.load(f)

key = {q['id']: q for q in data['questions']}

correct, total = 0, 0
cat_stats = {}
print('=== %s ===' % LABEL)
print('%-10s %-6s %-4s %-4s %s' % ('ID', 'Cat', 'Mine', 'Real', 'Result'))
print('-' * 46)
for qid, a in mine.items():
    real = key[qid]['answer']
    cat = key[qid].get('category', '?')
    ok = a['answer'] == real
    total += 1
    correct += ok
    cat_stats.setdefault(cat, {'t': 0, 'c': 0})
    cat_stats[cat]['t'] += 1
    cat_stats[cat]['c'] += ok
    print('%-10s %-6s %-4s %-4s %s' % (qid, cat, a['answer'], real, 'OK' if ok else 'X'))

print('-' * 46)
print('Overall: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
for cat, st in sorted(cat_stats.items()):
    print('  %s: %d/%d' % (cat, st['c'], st['t']))
