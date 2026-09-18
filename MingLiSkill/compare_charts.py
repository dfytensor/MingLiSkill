# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fa = json.load(open(r'E:\ming_li_skill\MingLiSkill\bench_source\fortune_api_results.json', encoding='utf-8'))
out = []
out.append('total iztro cases: %d' % len(fa))

case = fa[0]
cid = case['case_id']
out.append('=== case_id: %s ===' % cid)
api = case.get('api_response', {})
if api.get('success') and api.get('data'):
    d = api['data'].get('data') or {}
    out.append('chineseDate: %s' % d.get('chineseDate'))
    out.append('time: %s' % d.get('time'))
    out.append('fiveElementsClass: %s' % d.get('fiveElementsClass'))
    out.append('zodiac: %s' % d.get('zodiac'))
    palaces = d.get('palaces') or []
    out.append('palaces: %d' % len(palaces))
    for p in palaces:
        name = p.get('name', '?')
        major = [s.get('name', '') for s in p.get('majorStars', []) if s.get('name')]
        minor = [s.get('name', '') for s in p.get('minorStars', []) if s.get('name')]
        brightness = [(s.get('name',''), s.get('brightness','')) for s in p.get('majorStars', []) if s.get('name')]
        out.append('  %s: major=%s minor=%s brightness=%s' % (name, major, minor, brightness))
    if palaces:
        s0 = palaces[0].get('majorStars', [{}])[0] if palaces[0].get('majorStars') else {}
        out.append('  star all fields: %s' % list(s0.keys()))
else:
    out.append('api_response not successful: %s' % json.dumps(api, ensure_ascii=False)[:200])

# Our tool comparison
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
htk = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
bi = None
for q in data['questions']:
    if q.get('case_id') == cid:
        bi = q['birth_info']
        break
if bi:
    out.append('\n=== Our chart ===')
    out.append('birth: %d-%d-%d %d时 %s' % (bi['year'], bi['month'], bi['day'], bi.get('hour',12), bi['gender']))
    r = json.loads(htk.get_bazi_chart(year=bi['year'], month=bi['month'], day=bi['day'],
                           hour=bi.get('hour', 12), gender=bi['gender']))
    out.append('our 四柱: %s' % json.dumps(r.get('四柱', {}), ensure_ascii=False))
    out.append('our 日主: %s(%s) %s' % (r.get('日主'), r.get('日主五行'), r.get('日主强弱')))
    z = json.loads(htk.analyze_question(
        year=bi['year'], month=bi['month'], day=bi['day'],
        hour=bi.get('hour', 12), gender=bi['gender'],
        category='事业', question='test', options_json='[]'))
    out.append('our ziwei: %s' % json.dumps(z.get('ziwei', {}), ensure_ascii=False)[:400])

with open(r'E:\ming_li_skill\MingLiSkill\chart_compare.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
