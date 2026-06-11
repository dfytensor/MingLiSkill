import json
import random
import sys
sys.path.insert(0, r'E:\ming_li_skill')
from tools.hybrid_tools import HybridMingliToolkit

with open(r'F:\牛逼模型\MingLi-Bench\data\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

random.seed(42)
sampled = random.sample(data['questions'], 10)

htk = HybridMingliToolkit()

output = []
for idx, q in enumerate(sampled):
    bi = q['birth_info']
    cat = q['category']
    opts = q['options']
    r = htk.analyze_question(
        year=bi['year'], month=bi['month'], day=bi['day'],
        hour=bi.get('hour', 12), gender=bi['gender'],
        category=cat, question=q['question'],
        options_json=json.dumps(opts, ensure_ascii=False)
    )
    d = json.loads(r)

    lines = []
    lines.append('=' * 70)
    lines.append('Q%d | ID: %s | Category: %s' % (idx + 1, q['id'], cat))
    lines.append('Birth: %s %d-%02d-%02d %d:00' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour', 12)))
    lines.append('Q: %s' % q['question'])
    for o in opts:
        lines.append('  %s. %s' % (o['letter'], o['text']))
    lines.append('')
    lines.append('--- Bazi ---')
    b = d['bazi']
    lines.append('SiZhu: %s' % json.dumps(b['四柱'], ensure_ascii=False))
    lines.append('RiZhu: %s(%s) | Strength: %s' % (b['日主'], b['日主五行'], b['日主强弱']))
    lines.append('YongShen: %s | JiShen: %s' % (b['喜用神'], b.get('忌神', [])))
    lines.append('WuXing: %s' % json.dumps(b['五行力量'], ensure_ascii=False))
    lines.append('ShiShen: %s' % json.dumps(b['十神'], ensure_ascii=False))
    if '大运' in b:
        lines.append('DaYun: %s' % json.dumps(b['大运'][:5], ensure_ascii=False))
    lines.append('')
    lines.append('--- ZiWei ---')
    z = d['ziwei']
    for k in ['命宫主星', '官禄宫主星', '夫妻宫主星', '财帛宫主星', '疾厄宫主星', '子女宫主星', '父母宫主星']:
        if k in z:
            lines.append('%s: %s' % (k, z[k]))
    lines.append('')
    if 'rules_suggestion' in d:
        lines.append('[REF] rules: %s' % d['rules_suggestion'])
    lines.append('')
    output.append('\n'.join(lines))

with open(r'E:\ming_li_skill\bench_10_data.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(output))

print('Done. 10 questions exported to bench_10_data.txt')
