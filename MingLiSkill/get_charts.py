import json, sys
sys.path.insert(0, r'E:\ming_li_skill')
from tools import HybridMingliToolkit

with open(r'E:\ming_li_skill\sampled_questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

htk = HybridMingliToolkit()
results = []

for i, q in enumerate(questions):
    bi = q['birth_info']
    print('='*60)
    print('Q%d: %s | %s' % (i+1, q['id'], q['category']))
    print('Birth: %s %d-%02d-%02d %d:00' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour', 12)))
    print('Question: %s' % q['question'])
    for o in q['options']:
        print('  %s. %s' % (o['letter'], o['text']))
    print('')

    r = htk.analyze_question(
        year=bi['year'], month=bi['month'], day=bi['day'],
        hour=bi.get('hour', 12), gender=bi['gender'],
        category=q['category'], question=q['question'],
        options_json=json.dumps(q['options'], ensure_ascii=False)
    )
    data = json.loads(r)

    print('--- Bazi ---')
    bz = data.get('bazi', {})
    print('  Four Pillars: %s' % json.dumps(bz.get('四柱', {}), ensure_ascii=False))
    print('  Day Master: %s (%s) Strength: %s' % (bz.get('日主', '?'), bz.get('日主五行', '?'), bz.get('日主强弱', '?')))
    wuxing = bz.get('五行力量', {})
    print('  Five Elements: %s' % json.dumps(wuxing, ensure_ascii=False))
    print('  Yong Shen: %s  Ji Shen: %s' % (bz.get('喜用神', []), bz.get('忌神', [])))
    shishen = bz.get('十神', {})
    print('  Ten Gods: %s' % json.dumps(shishen, ensure_ascii=False))
    dayun = bz.get('大运', [])
    if dayun:
        print('  Dayun (first 5):')
        for d in dayun[:5]:
            print('    %s (age %d-%d)' % (d.get('ganzhi', '?'), d.get('start_age', 0), d.get('end_age', 0)))

    print('--- Ziwei ---')
    zw = data.get('ziwei', {})
    for k, v in zw.items():
        print('  %s: %s' % (k, v))

    print('--- Analysis ---')
    for k, v in data.items():
        if k not in ['bazi', 'ziwei', 'category']:
            print('  %s: %s' % (k, v))

    print('--- Rules Suggestion: %s ---' % data.get('rules_suggestion', {}).get('suggested_answer', 'N/A'))

    results.append(data)
    print('')

with open(r'E:\ming_li_skill\chart_data.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('Done. %d charts saved.' % len(results))
