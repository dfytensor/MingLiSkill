# -*- coding: utf-8 -*-
"""Post-scoring audit: inspect the real answer option texts (test already scored)."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
ids = ['ftb_0109', 'ftb_0003', 'ftb_0016', 'ftb_0028', 'ftb_0002', 'ftb_0065',
       'ftb_0019', 'ftb_0119', 'ftb_0148', 'ftb_0077', 'ftb_0048', 'ftb_0071']
for qid in ids:
    q = key[qid]
    real = q['answer']
    opt = next((o['text'] for o in q['options'] if o['letter'] == real), '?')
    print('%s [%s] real=%s: %s' % (qid, q['category'], real, opt[:80]))
