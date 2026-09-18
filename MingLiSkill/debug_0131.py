# -*- coding: utf-8 -*-
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.calendar_engine import shi_shen

HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v3.json', encoding='utf-8'))

q = by_id['ftb_0131']
bi = q['birth_info']
opts = q['options']
my = BASE['ftb_0131']
r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
    hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
    question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
b = json.loads(r).get('bazi', {})
day_gan = b.get('日主')
out = ['day=%s my=%s real=%s' % (day_gan, my, q['answer'])]
mq = re.search(r'(19|20)\d\d', q['question'])
year_opt = None
if mq:
    year_opt = (None, int(mq.group(0)), q['question'])
else:
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m:
            year_opt = (o['letter'], int(m.group(0)), o['text'])
            break
out.append('year_opt=%s' % (year_opt,))
y = year_opt[1]
gz = ['甲子','乙丑','丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉',
      '甲戌','乙亥','丙子','丁丑','戊寅','己卯','庚辰','辛巳','壬午','癸未',
      '甲申','乙酉','丙戌','丁亥','戊子','己丑','庚寅','辛卯','壬辰','癸巳',
      '甲午','乙未','丙申','丁酉','戊戌','己亥','庚子','辛丑','壬寅','癸卯',
      '甲辰','乙巳','丙午','丁未','戊申','己酉','庚戌','辛亥','壬子','癸丑',
      '甲寅','乙卯','丙辰','丁巳','戊午','己未','庚申','辛酉','壬戌','癸亥'][(y-4)%60]
ss_g = shi_shen(day_gan, gz[0])
out.append('y=%d gz=%s ss_g=%s' % (y, gz, ss_g))
alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)
out.append('alltxt has 父亲: %s' % ('父亲' in alltxt))
zhi = gz[1]
mid = {'丑':('己','癸','辛')}.get(zhi, (None,))[1]
out.append('zhi=%s mid=%s mid_ss=%s' % (zhi, mid, shi_shen(day_gan, mid) if mid else None))
for o in opts:
    hit = ('父亲' in o['text'] and any(k in o['text'] for k in ['去世','离世','亡']))
    out.append('  %s hit=%s | %s' % (o['letter'], hit, o['text'][:40]))
open(r'E:\ming_li_skill\MingLiSkill\debug_0131.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
