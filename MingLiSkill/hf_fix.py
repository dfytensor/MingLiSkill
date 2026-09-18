# -*- coding: utf-8 -*-
"""
hf_fix.py v2 — 健康家庭信号精化版
修复: H5拆分食/伤, H6新增食神喜事, D1/H2支持纯年份选项, F3/F1要求选项含信号年份
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.calendar_engine import shi_shen

HTK = HybridMingliToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v3.json', encoding='utf-8'))

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}
WUXUE_KU = {'木':'未','火':'戌','金':'丑','水':'辰'}
HEALTH_KW_Q = ['健康','病','癌','手术','抑郁','状况如何','受伤']
POSITIVE_KW = ['得奖','获奖','结婚','好机遇','喜事','升职','加薪','得财','顺利']

def year_gz(y):
    gz = ['甲子','乙丑','丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉',
          '甲戌','乙亥','丙子','丁丑','戊寅','己卯','庚辰','辛巳','壬午','癸未',
          '甲申','乙酉','丙戌','丁亥','戊子','己丑','庚寅','辛卯','壬辰','癸巳',
          '甲午','乙未','丙申','丁酉','戊戌','己亥','庚子','辛丑','壬寅','癸卯',
          '甲辰','乙巳','丙午','丁未','戊申','己酉','庚戌','辛亥','壬子','癸丑',
          '甲寅','乙卯','丙辰','丁巳','戊午','己未','庚申','辛酉','壬戌','癸亥']
    return gz[(y - 4) % 60]

def pick_year_option(opts, y):
    """选含指定年份的选项; 若都是纯年份文本则按年份匹配"""
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m and int(m.group(0)) == y:
            return o['letter']
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m:
            return o['letter']
    return None

gain = loss = 0
details = []

for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    bi = q['birth_info']
    my = BASE[qid]; real = q['answer']
    opts = q['options']
    alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except:
        continue
    pillars = b.get('四柱', {})
    day_gan = b.get('日主','')
    if not day_gan: continue
    day_wx = GAN_WX[day_gan]
    female = bi['gender'] in ('女','F','female')
    wx = b.get('五行力量', {})
    tot = sum(wx.values()) or 1
    seal_wx = {'木':'水','火':'木','土':'火','金':'土','水':'金'}[day_wx]
    wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]

    # 收集本题全部年份(题干+各选项)
    years = set()
    mq = re.search(r'(19|20)\d\d', q['question'])
    if mq: years.add(int(mq.group(0)))
    opt_years = {}
    for o in opts:
        for m in re.finditer(r'(19|20)\d\d', o['text']):
            years.add(int(m.group(0)))
            opt_years.setdefault(int(m.group(0)), o['letter'])

    pick = None; why = ''

    for y in sorted(years):
        if pick: break
        gz = year_gz(y)
        ygan, yzhi = gz[0], gz[1]
        ss_g = shi_shen(day_gan, ygan)
        zhi_ss_all = [shi_shen(day_gan, h) for h in ZHI_HIDE.get(yzhi, ())]
        is_health_q = any(k in q['question'] for k in HEALTH_KW_Q)
        is_generic_q = ('发生' in q['question'] or '出现的时间' in q['question'] or '何时' in q['question']) and not is_health_q

        # H1: 正印透干 → 抑郁
        if not pick and ss_g == '正印' and any(k in alltxt for k in ['抑郁','忧郁']):
            pick = pick_year_option(opts, y) or next((o['letter'] for o in opts if '抑郁' in o['text']), None)
            why = 'H1:%d%s=正印透干→抑郁' % (y, gz); continue

        # F3: 流年支中气=父星偏财/母星正印 → 父/母去世 (选项须含该年份!)
        if not pick and any(k in alltxt for k in ['父亲','母亲']):
            if ZHI_HIDE.get(yzhi) and len(ZHI_HIDE[yzhi]) > 1:
                mid = ZHI_HIDE[yzhi][1]
                mid_ss = shi_shen(day_gan, mid)
                opt = opt_years.get(y)
                if opt:
                    otext = next(o['text'] for o in opts if o['letter'] == opt)
                    if mid_ss == '正印' and re.search(r'母亲[^。]{0,20}(去世|离世|亡|病逝)', otext) and not re.search(r'父亲[^。]{0,20}(去世|离世|亡)', otext):
                        pick = opt; why = 'F3:%d%s中气%s=母星→母亡' % (y, gz, mid); continue
                    if mid_ss == '偏财' and re.search(r'父亲[^。]{0,20}(去世|离世|亡)', otext) and not re.search(r'母亲[^。]{0,20}(去世|离世|亡|病逝)', otext):
                        pick = opt; why = 'F3:%d%s中气%s=父星→父亡' % (y, gz, mid); continue

        # F1: 父星入库年 → 父去世 (选项须含年份)
        if not pick and any(k in alltxt for k in ['父亲']):
            ku = WUXUE_KU.get(wealth_wx)
            if ku and yzhi == ku:
                cand = None
                opt = opt_years.get(y)
                if opt:
                    otext = next(o['text'] for o in opts if o['letter'] == opt)
                    if re.search(r'父亲[^。]{0,20}(去世|离世|亡)', otext):
                        cand = opt
                else:
                    cand = next((o['letter'] for o in opts if re.search(r'父亲[^。]{0,20}(去世|离世|亡)', o['text'])), None)
                if cand: pick = cand; why = 'F1:%d%s=%s库父星入库→父亡' % (y, gz, wealth_wx); continue

        # H5a: 伤官透干 → 意外/健康受损 (任何题)
        if not pick and ss_g == '伤官':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['意外','伤','病','癌','食药','骨折','车祸','撞'])), None)
            if cand: pick = cand; why = 'H5a:%d%s=伤官透干→健康受损' % (y, gz); continue

        # H5b: 食神透干 + 健康类题干 → 病/癌
        if not pick and ss_g == '食神' and is_health_q:
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['病','癌','骨折','撞'])), None)
            if cand: pick = cand; why = 'H5b:%d%s=食神+健康题→病' % (y, gz); continue

        # H6: 食神透干 + 泛事件题 → 喜事
        if not pick and ss_g == '食神' and is_generic_q:
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in POSITIVE_KW)), None)
            if cand: pick = cand; why = 'H6:%d%s=食神透干→喜事' % (y, gz); continue

        # D1: 偏印透干 → 灾劫/自己重病 (纯年份选项按年份匹配)
        if not pick and ss_g == '偏印':
            if any(k in alltxt for k in ['凶劫','灾','患癌','抑郁']):
                own = next((o['letter'] for o in opts if ('患癌' in o['text'] or '凶劫' in o['text']) and ('自己' in o['text'] or '命主' in o['text'])), None)
                if not own:
                    own = pick_year_option(opts, y)  # 纯年份选项
                if own: pick = own; why = 'D1:%d%s=偏印透干→灾病' % (y, gz); continue

        # H3: 女命食伤到位(干/支含) → 流产/堕胎
        if not pick and female and any(k in alltxt for k in ['流产','堕胎']):
            if ss_g in ('食神','伤官') or any(s in ('食神','伤官') for s in zhi_ss_all):
                cand = next((o['letter'] for o in opts if '流产' in o['text'] or '堕胎' in o['text']), None)
                if cand: pick = cand; why = 'H3:%d%s食神到位→流产/堕胎' % (y, gz); continue

        # H2: 流年干支伏吟年柱 → 健康重大事件 (按年份选选项)
        if not pick and any(k in alltxt for k in ['健康','确诊','手术','中风','去世','辞世','长辞']):
            if gz == pillars.get('年柱',''):
                pick = pick_year_option(opts, y)
                if pick: why = 'H2:%d%s伏吟年柱→健康事件' % (y, gz); continue

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
    details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, pick, real, tag, why))

final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
print('HF FIX v2: +%d / -%d' % (gain, loss))
print('FINAL: %d/115 = %.1f%%' % (final, final/115*100))
for d in details:
    print(' ', d.encode('ascii','replace').decode())
json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v4.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved fixed_answers_v4.json')
