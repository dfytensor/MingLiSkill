import json, random, sys
sys.path.insert(0, r'E:\ming_li_skill')
from tools.hybrid_tools import HybridMingliToolkit

with open(r'F:\牛逼模型\MingLi-Bench\data\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Total questions: %d' % len(data['questions']))

random.seed(888)
sampled = random.sample(data['questions'], 10)

htk = HybridMingliToolkit()

output = []
for idx, q in enumerate(sampled):
    bi = q['birth_info']
    opts = q['options']
    cat = q['category']
    qid = q['id']
    qtext = q['question']
    print('#%d %s [%s] %s' % (idx + 1, qid, cat, qtext[:60]))
    r = htk.analyze_question(
        year=bi['year'], month=bi['month'], day=bi['day'],
        hour=bi.get('hour', 12), gender=bi['gender'],
        category=cat, question=qtext,
        options_json=json.dumps(opts, ensure_ascii=False)
    )
    d = json.loads(r)
    item = {
        'idx': idx + 1,
        'id': qid,
        'category': cat,
        'birth_info': bi,
        'question': qtext,
        'options': opts,
        'chart_data': d
    }
    output.append(item)

with open(r'E:\ming_li_skill\blind_10_charts.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print('\nSampled %d questions. Charts saved.' % len(output))
