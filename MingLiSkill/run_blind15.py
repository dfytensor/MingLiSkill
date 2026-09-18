"""Blind test: sample N questions WITHOUT answers, generate charts.
Non-cheating protocol: answers never exported. Score later via score_blind15.py
Usage: python run_blind15.py [seed] [n] [outprefix]
"""
import json, random, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import HybridMingliToolkit

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20260918
n = int(sys.argv[2]) if len(sys.argv) > 2 else 15
prefix = sys.argv[3] if len(sys.argv) > 3 else 'blind15'

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Exclude questions already used (and thus already seen answers) in prior rounds
EXCLUDE = set()
EX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'used_ids.json')
if os.path.exists(EX_FILE):
    with open(EX_FILE, encoding='utf-8') as f:
        EXCLUDE = set(json.load(f))

random.seed(seed)
pool = [q for q in data['questions'] if q['id'] not in EXCLUDE]
sampled = random.sample(pool, n)

# record used ids
used = sorted(EXCLUDE | {q['id'] for q in sampled})
with open(EX_FILE, 'w', encoding='utf-8') as f:
    json.dump(used, f, ensure_ascii=False)

htk = HybridMingliToolkit()

questions_out = []
for idx, q in enumerate(sampled):
    bi = q['birth_info']
    cat = q['category']
    opts = q['options']
    qtext = q['question']
    r = htk.analyze_question(
        year=bi['year'], month=bi['month'], day=bi['day'],
        hour=bi.get('hour', 12), gender=bi['gender'],
        category=cat, question=qtext,
        options_json=json.dumps(opts, ensure_ascii=False)
    )
    d = json.loads(r)
    item = {
        'idx': idx + 1,
        'id': q['id'],
        'category': cat,
        'birth_info': bi,
        'question': qtext,
        'options': opts,
        'chart_data': d,
    }
    questions_out.append(item)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), prefix + '_charts.json'), 'w', encoding='utf-8') as f:
    json.dump(questions_out, f, ensure_ascii=False, indent=2)

ids = [q['id'] for q in sampled]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), prefix + '_ids.json'), 'w', encoding='utf-8') as f:
    json.dump(ids, f, ensure_ascii=False)

print('Sampled %d questions (blind, no answers exported).' % len(questions_out))
print('IDs:', ','.join(ids))
