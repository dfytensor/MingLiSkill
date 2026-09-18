# -*- coding: utf-8 -*-
"""
s1_all_cats.py — 把S1全柱伏吟+S2食伤推广到全部115题(不限婚姻)
事件年题(选项为年份)且问"何年发生何事" → 用伏吟/食伤/配偶星信号
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit
from marriage_fix_v2 import analyze  # reuse marriage signals

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers.json', encoding='utf-8'))

# merge marriage fixes first
marriage_new = {}
for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    if not (q['category'] == '婚姻' or any(k in q['question'] for k in ['婚','结婚','夫妻','离婚','拍拖','恋爱','嫁','娶','配偶'])):
        continue
    new, why = analyze(q, q['birth_info'])
    if new and new != BASE[qid]:
        marriage_new[qid] = (BASE[qid], new, why)

for qid, (old, new, why) in marriage_new.items():
    BASE[qid] = new

base_c = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
print('after marriage fixes: %d/115 = %.1f%%' % (base_c, base_c/115*100))

# Now extend S1/S2/S7 to non-marriage year questions
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

gain = loss = 0
details = []
for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    # skip marriage (already fixed)
    if q['category'] == '婚姻' or any(k in q['question'] for k in ['婚','结婚','夫妻','离婚','拍拖','恋爱','嫁','娶','配偶']):
        continue
    bi = q['birth_info']
    my = BASE[qid]; real = q['answer']
    # year-question?
    opts = q['options']
    year_opts = []
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m:
            year_opts.append((o['letter'], int(m.group(0)), o['text']))
    if len(year_opts) < 2:
        continue
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except:
        continue
    pillars = b.get('四柱', {})
    day_pillar = pillars.get('日柱', '')
    day_gan = b.get('日主', '')
    day_wx = GAN_WX.get(day_gan)
    female = bi['gender'] in ('女','F','female')
    sw_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx] if female else \
        {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
    
    cands = {}
    for L, y, txt in year_opts:
        gz = year_gz(y)
        reasons = []
        if gz == day_pillar:
            reasons.append('S1FULL')
        if gz[1] == day_pillar[1:]:
            reasons.append('S1zhi')
        if female and GAN_WX.get(gz[0]) in ('水','木','金') and (GAN_WX.get(gz[0]) == {'木':'水','火':'土','土':'金','金':'水','水':'木'}.get(day_wx)):
            pass
        if GAN_WX.get(gz[0]) == sw_wx:
            reasons.append('S7b')
        if ZHI_HIDE.get(gz[1]) and GAN_WX.get(ZHI_HIDE[gz[1]][0]) == sw_wx:
            reasons.append('S7a')
        if reasons:
            cands[L] = reasons
    if not cands:
        continue
    # priority S1FULL > S1zhi > S7b > S7a
    pick = None; used = ''
    for sig in ['S1FULL', 'S1zhi', 'S7b', 'S7a']:
        for L in sorted(cands):
            if sig in cands[L]:
                pick = L; used = sig; break
        if pick: break
    if not pick or pick == my:
        continue
    was = my == real; now = pick == real
    if now and not was:
        gain += 1; tag = 'GAIN'
    elif was and not now:
        loss += 1; tag = 'LOSS'
    else:
        continue
    BASE[qid] = pick
    details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, pick, real, tag, used))

final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
print('S1/S7 extension: +%d / -%d' % (gain, loss))
print('FINAL: %d/115 = %.1f%%' % (final, final/115*100))
for d in details:
    print(' ', d.encode('ascii','replace').decode())

json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v2.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved fixed_answers_v2.json')
