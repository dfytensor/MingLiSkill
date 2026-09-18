# -*- coding: utf-8 -*-
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.calendar_engine import shi_shen

HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}

def year_gz(y):
    gz = ['甲子','乙丑','丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉',
          '甲戌','乙亥','丙子','丁丑','戊寅','己卯','庚辰','辛巳','壬午','癸未',
          '甲申','乙酉','丙戌','丁亥','戊子','己丑','庚寅','辛卯','壬辰','癸巳',
          '甲午','乙未','丙申','丁酉','戊戌','己亥','庚子','辛丑','壬寅','癸卯',
          '甲辰','乙巳','丙午','丁未','戊申','己酉','庚戌','辛亥','壬子','癸丑',
          '甲寅','乙卯','丙辰','丁巳','戊午','己未','庚申','辛酉','壬戌','癸亥']
    return gz[(y - 4) % 60]

out = []
for qid in ['ftb_0131', 'ftb_0094', 'ftb_0060']:
    q = by_id[qid]
    bi = q['birth_info']
    opts = q['options']
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except Exception as e:
        b = {}
        out.append('%s bazi ERR %s' % (qid, e))
        continue
    day_gan = b.get('日主','')
    pillars = b.get('四柱', {})
    out.append('%s day=%s yearpillar=%s' % (qid, day_gan, pillars.get('年柱')))
    mq = re.search(r'(19|20)\d\d', q['question'])
    out.append('  year in question: %s' % (mq.group(0) if mq else None))
    year_opt = None
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m:
            year_opt = (o['letter'], int(m.group(0)), o['text'])
            break
    out.append('  first year option: %s' % (year_opt,))
    y = year_opt[1] if year_opt else None
    if y:
        gz = year_gz(y)
        out.append('  gz(%d)=%s  ss(gan)=%s  zhihide=%s mid_ss=%s' % (
            y, gz, shi_shen(day_gan, gz[0]), ZHI_HIDE.get(gz[1]),
            shi_shen(day_gan, ZHI_HIDE[gz[1]][1]) if len(ZHI_HIDE.get(gz[1], ())) > 1 else None))

open(r'E:\ming_li_skill\MingLiSkill\debug3.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
