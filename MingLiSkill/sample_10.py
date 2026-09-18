import json, random

with open(r'F:\牛逼模型\MingLi-Bench\data\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data['questions'])
print('Total questions:', total)

random.seed(42)
sampled = random.sample(data['questions'], 10)

for i, q in enumerate(sampled):
    bi = q['birth_info']
    print('')
    print('=== Q%s: %s | Cat: %s ===' % (i+1, q['id'], q['category']))
    print('Birth: %s %d-%02d-%02d %d:00' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour', 12)))
    print('Question: %s' % q['question'])
    for o in q['options']:
        print('  %s. %s' % (o['letter'], o['text']))

with open(r'E:\ming_li_skill\sampled_ids.json', 'w', encoding='utf-8') as f:
    json.dump([q['id'] for q in sampled], f, ensure_ascii=False)

with open(r'E:\ming_li_skill\sampled_questions.json', 'w', encoding='utf-8') as f:
    json.dump(sampled, f, ensure_ascii=False, indent=2)
