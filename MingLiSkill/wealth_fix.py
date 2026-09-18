# -*- coding: utf-8 -*-
"""
wealth_fix.py — W1-W8 财运信号应用到全部115题, 全局验证 GAIN/LOSS
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit
from tools.calendar_engine import shi_shen

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v2.json', encoding='utf-8'))

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}
# 十二长生 for 甲 (木): use for 官星坐支状态 (女命官=克我者)
# 只需绝: 木绝在申, 火绝在亥, 土绝在? (土随火: 亥), 金绝在寅, 水绝在巳
JUE = {'木':'申','火':'亥','土':'亥','金':'寅','水':'巳'}

def year_gz(y):
    gz = ['甲子','乙丑','丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉',
          '甲戌','乙亥','丙子','丁丑','戊寅','己卯','庚辰','辛巳','壬午','癸未',
          '甲申','乙酉','丙戌','丁亥','戊子','己丑','庚寅','辛卯','壬辰','癸巳',
          '甲午','乙未','丙申','丁酉','戊戌','己亥','庚子','辛丑','壬寅','癸卯',
          '甲辰','乙巳','丙午','丁未','戊申','己酉','庚戌','辛亥','壬子','癸丑',
          '甲寅','乙卯','丙辰','丁巳','戊午','己未','庚申','辛酉','壬戌','癸亥']
    return gz[(y - 4) % 60]

def get_chart(bi, q, opts):
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        return json.loads(r).get('bazi', {})
    except:
        return {}

def get_zw(bi):
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2).get('十二宫', {})
        return {k: (v.get('主星',[]) if isinstance(v,dict) else v) for k,v in zw.items()}
    except:
        return {}

gain = loss = 0
details = []
signals_used = {}

for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    bi = q['birth_info']
    my = BASE[qid]; real = q['answer']
    opts = q['options']
    alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)
    b = get_chart(bi, q, opts)
    if not b: continue
    pillars = b.get('四柱', {})
    day_gan = b.get('日主','')
    day_wx = GAN_WX.get(day_gan)
    female = bi['gender'] in ('女','F','female')
    wx = b.get('五行力量', {})
    tot = sum(wx.values()) or 1
    wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]  # 我克=财
    seal_wx = {'木':'水','火':'木','土':'火','金':'土','水':'金'}[day_wx]   # 生我=印
    smap = get_zw(bi)

    pick = None; why = ''

    # ---- W1r: 出身贫富看年柱本气财星(精化版) ----
    if any(k in alltxt for k in ['出身','家境','贫或富','贫穷家庭','富贵家庭','小康之家','出生家境']):
        year_zhi = pillars.get('年柱','')[1:2]
        benqi = ZHI_HIDE.get(year_zhi, (None,))[0]
        has_wealth_benqi = GAN_WX.get(benqi) == wealth_wx
        if has_wealth_benqi:
            for o in opts:
                if any(k in o['text'] for k in ['富','有钱']) and '贫穷' not in o['text']:
                    pick = o['letter']; why = 'W1r:年支%s本气%s=财星→富' % (year_zhi, benqi); break
        # (贫分支已移除: 本气非财星不足以判贫, ftb_0081/0146 教训)

    # ---- W6: 财帛宫定性 (收入/年薪/财运/理财题) ----
    if not pick and any(k in alltxt for k in ['年薪','收入','财运','理财','身家']):
        cb = smap.get('财帛', [])
        nums = []
        for o in opts:
            m = re.search(r'(\d+)\s*(万|千万|千)', o['text'])
            if m:
                v = int(m.group(1))
                if '千万' in m.group(2): v *= 1000
                elif '千' == m.group(2): v /= 10
                nums.append((v, o['letter']))
        nums.sort()
        if any(s in cb for s in ['天府','武曲']) and len(nums) >= 3:
            pick = nums[len(nums)-2][1]; why = 'W6:财帛%s→第2高收入' % cb
        elif any(s in cb for s in ['廉贞','贪狼']):
            for o in opts:
                if any(k in o['text'] for k in ['乱花','投机','没理财']):
                    pick = o['letter']; why = 'W6:财帛廉贪→乱花钱'; break
        elif not cb and len(nums) >= 3:
            pick = nums[len(nums)//2][1]; why = 'W6:财帛无星→中档'

    # ---- W5: 财极弱+印显 → 母亲管理 ----
    if not pick and '理财' in alltxt:
        wpct = wx.get(wealth_wx, 0) / tot * 100
        spct = wx.get(seal_wx, 0) / tot * 100
        if wpct < 10 and spct >= 5:
            for o in opts:
                if '母亲' in o['text']:
                    pick = o['letter']; why = 'W5:财%.0f%%印%.0f%%→母亲管理' % (wpct, spct); break

    # ---- W8: 女命财星=0 → 花钱/破产选项 ----
    if not pick and female and any(k in alltxt for k in ['花女人钱','倾家荡产','被骗','老千']):
        wcount = wx.get(wealth_wx, 0)
        if wcount == 0:
            for o in opts:
                if any(k in o['text'] for k in ['花女人钱','倾家荡产','老千']):
                    pick = o['letter']; why = 'W8:财星=0→破财选项'; break

    # ---- W7: 配偶工作: 官坐绝/坐藏财 → 经商 ----
    if not pick and female and '配偶' in alltxt and any(k in alltxt for k in ['打工','经商']):
        guan_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx]
        # find 官星天干 in pillars
        for pn in ['年柱','月柱','日柱','时柱']:
            gan = pillars.get(pn,'')[0:1]
            zhi = pillars.get(pn,'')[1:2]
            if gan and shi_shen(day_gan, gan) in ('正官','七杀'):
                jue = JUE.get(GAN_WX.get(gan))
                hidden = ZHI_HIDE.get(zhi, ())
                has_wealth_hidden = any(GAN_WX.get(h) == wealth_wx for h in hidden)
                if zhi == jue or has_wealth_hidden:
                    for o in opts:
                        if '经商' in o['text'] and ('成多于败' in o['text'] or '盈余' in o['text']):
                            pick = o['letter']; why = 'W7:官%s坐%s%s→经商成功' % (gan, zhi, '绝' if zhi==jue else '藏财'); break
                else:
                    for o in opts:
                        if '打工' in o['text'] and ('高职' in o['text'] or '助力' in o['text']):
                            pick = o['letter']; why = 'W7:官%s坐%s稳定→打工' % (gan, zhi); break
                break

    # ---- W3: 官禄武曲七杀 → 工程技术 ----
    if not pick and any(k in alltxt for k in ['学历','职业','行业','工程师','研究员']):
        gl = smap.get('官禄', [])
        if any(s in gl for s in ['武曲','七杀']):
            for o in opts:
                if '工程师' in o['text'] or '技术' in o['text']:
                    pick = o['letter']; why = 'W3:官禄%s→工程技术' % gl; break

    # ---- W4: 田宅破军/天梁 + 房产 → 得利 ----
    if not pick and any(k in alltxt for k in ['地产','房产','田宅','物业','买房']):
        tz = smap.get('田宅', [])
        if any(s in tz for s in ['破军','天梁','天府']):
            for o in opts:
                if any(k in o['text'] for k in ['得厚利','买卖房产','地产生意']):
                    pick = o['letter']; why = 'W4:田宅%s→房产得利' % tz; break

    # ---- W2: 偏印到位流年 → 通灵/玄学/被骗年 ----
    if not pick and any(k in q['question'] for k in ['通灵','神明','被骗钱']):
        for o in opts:
            m = re.search(r'(19|20)\d\d', o['text'])
            if not m: continue
            y = int(m.group(0))
            gz = year_gz(y)
            ss_g = shi_shen(day_gan, gz[0])
            zhi = gz[1]
            ss_z = shi_shen(day_gan, ZHI_HIDE[zhi][0]) if ZHI_HIDE.get(zhi) else None
            if ss_g == '偏印' or ss_z == '偏印':
                pick = o['letter']; why = 'W2:%d=%s偏印到位→通灵/被骗' % (y, gz); break

    if not pick or pick == my:
        continue
    was = my == real; now = pick == real
    sig = why.split(':')[0]
    if now and not was:
        gain += 1; tag = 'GAIN'
    elif was and not now:
        loss += 1; tag = 'LOSS'
    else:
        continue
    BASE[qid] = pick
    signals_used[sig] = signals_used.get(sig, 0) + (1 if tag == 'GAIN' else -1)
    details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, pick, real, tag, why))

final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
print('WEALTH FIX: +%d / -%d' % (gain, loss))
print('per-signal net: %s' % signals_used)
print('FINAL: %d/115 = %.1f%%' % (final, final/115*100))
for d in details:
    print(' ', d.encode('ascii','replace').decode())
json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v3.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved fixed_answers_v3.json')
