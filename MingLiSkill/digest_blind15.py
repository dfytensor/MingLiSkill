"""Print compact per-question digest for blind reasoning (no answers)."""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PREFIX = sys.argv[3] if len(sys.argv) > 3 else 'blind15'
with open(r'E:\ming_li_skill\MingLiSkill\%s_charts.json' % PREFIX, 'r', encoding='utf-8') as f:
    qs = json.load(f)

START = int(sys.argv[1]) if len(sys.argv) > 1 else 1
END = int(sys.argv[2]) if len(sys.argv) > 2 else len(qs)

for q in qs:
    if not (START <= q['idx'] <= END):
        continue
    bi = q['birth_info']
    d = q['chart_data']
    print('=' * 78)
    print('Q%d | ID: %s | Cat: %s | Gender: %s | %d-%02d-%02d %02d:%02d | %s' % (
        q['idx'], q['id'], q['category'], bi['gender'], bi['year'], bi['month'],
        bi['day'], bi.get('hour', 12), bi.get('minute', 0), bi.get('raw', '')))
    print('Q: %s' % q['question'])
    for o in q['options']:
        print('  %s. %s' % (o['letter'], o['text']))

    b = d['bazi']
    print('--- BAZI ---')
    print('SiZhu: %s' % json.dumps(b['四柱'], ensure_ascii=False))
    print('RiZhu: %s(%s) | Strength: %s' % (b['日主'], b['日主五行'], b['日主强弱']))
    print('WuXing: %s' % json.dumps(b['五行力量'], ensure_ascii=False))
    print('Yong: %s | Ji: %s' % (b['喜用神'], b.get('忌神', [])))
    print('KongWang: %s' % json.dumps(b.get('空亡', []), ensure_ascii=False))
    print('ShiShen: %s' % json.dumps(b['十神'], ensure_ascii=False))
    dy = b.get('大运', [])
    if dy:
        print('DaYun: %s' % '; '.join('%s(%s-%s)' % (x.get('干支', x.get('ganzhi', '?')), x.get('起运年龄', '?'), x.get('止运年龄', '?')) for x in dy))
    for k in ['大运', '起运', '五行占比']:
        if k in b:
            print('%s: %s' % (k, json.dumps(b[k], ensure_ascii=False)))

    z = d.get('ziwei', {})
    print('--- ZIWEI ---')
    for k, v in z.items():
        print('  %s: %s' % (k, json.dumps(v, ensure_ascii=False)))

    print('--- CATEGORY ANALYSES ---')
    for k, v in d.items():
        if k in ('category', 'bazi', 'ziwei', 'qimen', 'rules_suggestion', 'note', 'liunian'):
            continue
        print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False)))

    ln = d.get('liunian', {})
    if ln:
        print('--- LIUNIAN ---')
        print('  detected years: %s' % ln.get('检测到的年份', []))
        for yi in ln.get('年份流年对比', []):
            print('  %s %s gan=%s zhi=%s tags=%s %s' % (
                yi['年份'], yi['干支'], yi.get('天干十神'), json.dumps(yi.get('地支藏干十神', []), ensure_ascii=False),
                json.dumps(yi.get('标签', []), ensure_ascii=False), yi.get('大运', '')))

    qm = d.get('qimen', {})
    if qm:
        print('--- QIMEN (compact) ---')
        for yr, qd in qm.items():
            keji = qd.get('keji', {})
            print('  %s: yongshen=%s fu=%s %s' % (yr, keji.get('用神'), keji.get('辅助'), keji.get('说明', '')))

    rs = d.get('rules_suggestion', {})
    print('--- rules_suggestion: %s (仅供参考) ---' % rs.get('suggested_answer'))
    print()
