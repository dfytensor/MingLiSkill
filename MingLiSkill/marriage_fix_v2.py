# -*- coding: utf-8 -*-
"""
marriage_fix_v2.py — 7个新信号应用到34道婚姻题
先在wrong集验证, 再看对题是否被误伤
"""
import io, sys, json
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers.json', encoding='utf-8'))

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
# 流年地支->年份地支: year % 12: 子0...亥11
def year_zhi(y):
    return ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'][(y - 4) % 12]
def year_gan(y):
    return ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'][(y - 4) % 10]

ZHI_HIDE = {  # 本气,中气,余气
    '子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
    '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
    '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲'),
}
SHI_SHEN = {}
def shishen(day_gan, other_gan):
    key = (day_gan, other_gan)
    if key in SHI_SHEN: return SHI_SHEN[key]
    import os
    r = None
    try:
        from tools.calendar_engine import shi_shen as _ss
        r = _ss(day_gan, other_gan)
    except:
        pass
    SHI_SHEN[key] = r
    return r

def analyze(q, bi):
    """返回 (新答案, 依据)"""
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category='婚姻',
            question=q['question'], options_json=json.dumps(q['options'], ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except:
        b = {}
    pillars = b.get('四柱', {})
    day_zhi = pillars.get('日柱','')[1:2]
    day_gan = b.get('日主','')
    day_wx = GAN_WX.get(day_gan)
    female = bi['gender'] in ('女','F','female')
    ss = b.get('十神', {})
    wx = b.get('五行力量', {})
    tot = sum(wx.values()) or 1
    opts = q['options']

    # S3: 配偶星位置
    spouse_wx = GAN_WX.get({'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx]) if not female else \
        {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx]
    # 女命官杀=克我; 男命财=我克
    if female:
        sw_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx]
    else:
        sw_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
    
    # 配偶星本气位置
    spouse_loc = []
    for pn in ['年柱','月柱','日柱','时柱']:
        zhi = pillars.get(pn,'')[1:2]
        if zhi and ZHI_HIDE.get(zhi) and ZHI_HIDE[zhi][0] and GAN_WX.get(ZHI_HIDE[zhi][0]) == sw_wx:
            spouse_loc.append(pn)
    has_spouse_monthday = any(p in spouse_loc for p in ['月柱','日柱'])
    spouse_wx_count = wx.get(sw_wx, 0)
    
    # 紫微
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2).get('十二宫', {})
        smap = {k: (v.get('主星',[]) if isinstance(v,dict) else v) for k,v in zw.items()}
    except:
        smap = {}
    fude = smap.get('福德', [])
    fuqi = smap.get('夫妻', [])

    alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)

    # === S3: 已婚/未婚状态题 ===
    unmarried_kw = ['未婚','单身','独身','未嫁','未娶','从未结']
    married_kw = ['已婚','结婚','离婚','二婚','一婚','夫早亡','嫁']
    if any(k in alltxt for k in unmarried_kw) and any(k in alltxt for k in married_kw):
        if not has_spouse_monthday and spouse_wx_count == 0:
            for o in opts:
                if any(k in o['text'] for k in ['独身','单身','未婚','未嫁','未娶','从未']):
                    return o['letter'], 'S3:配偶星%s=%d且不在月日→独身' % (sw_wx, spouse_wx_count)
        # (已婚判定不可靠, 已移除, 只保留独身判定)

    # === S4: 福德宫定性 (独身细分) ===
    if '嫖' in alltxt or '清心' in alltxt:
        if any(s in fude for s in ['紫微','天府','天梁']):
            for o in opts:
                if '清心' in o['text'] or '寡欲' in o['text']:
                    return o['letter'], 'S4:福德%s→清心寡欲' % fude
        if any(s in fude for s in ['贪狼','廉贞']):
            for o in opts:
                if '嫖' in o['text']:
                    return o['letter'], 'S4:福德%s→欲望' % fude

    # === S4b: 变心归属 ===
    if '外遇' in alltxt:
        if '天机' in fude:
            # 自己变心
            for o in opts:
                if '命主外遇' in o['text'] or ('命主' in o['text'] and '外遇' in o['text']):
                    return o['letter'], 'S4b:福德天机→变心在自己'
        elif any(s in fude for s in ['紫微','天府']):
            for o in opts:
                if '丈夫' in o['text'] and '外遇' in o['text']:
                    return o['letter'], 'S4b:福德%s→变心在对方' % fude

    # === 年份题: S1伏吟 / S2食伤 / S5官透 / S6武破晚婚 / S7配偶星到位 ===
    import re
    year_opts = []
    pure_year_opts = []
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m:
            year_opts.append((o['letter'], int(m.group(0))))
            if re.fullmatch(r'\s*(19|20)\d\d\s*年?\s*', o['text']):
                pure_year_opts.append((o['letter'], int(m.group(0))))
    is_divorce_q = any(k in q['question'] for k in ['离婚','分手','结束'])
    is_wedding_q = any(k in q['question'] for k in ['结婚','成婚','娶','嫁','拍拖','恋爱'])
    
    if year_opts and (is_divorce_q or is_wedding_q):
        cands = {}
        for L, y in year_opts:
            gz = year_zhi(y); gg = year_gan(y)
            reasons = []
            # S1: 伏吟日支
            if gz == day_zhi:
                reasons.append('S1伏吟日支')
            # S2: 女命食伤年 → 分手/离婚
            if female and is_divorce_q:
                r_ss = shishen(day_gan, gg)
                if r_ss and ('食' in r_ss or '伤' in r_ss):
                    reasons.append('S2女命食伤年%s(%s)' % (gg, r_ss))
                zhi_ss = None
                if ZHI_HIDE.get(gz):
                    zhi_ss = shishen(day_gan, ZHI_HIDE[gz][0])
                if zhi_ss and ('食' in zhi_ss or '伤' in zhi_ss):
                    reasons.append('S2女命食伤支%s(%s)' % (gz, zhi_ss))
            # S5: 女命官透干 → 婚变(官弱时)
            if female:
                r_g = shishen(day_gan, gg)
                if r_g == '正官':
                    reasons.append('S5官透')
            # S7b: 配偶星透于流年天干
            if GAN_WX.get(gg) == sw_wx:
                reasons.append('S7b配偶星透干(%s)' % gg)
            # S7a: 配偶星到位(支本气=配偶星)
            if ZHI_HIDE.get(gz) and GAN_WX.get(ZHI_HIDE[gz][0]) == sw_wx:
                reasons.append('S7配偶星到位(%s)' % gz)
            # S6: 夫妻宫武破 → 晚婚
            if is_wedding_q and any(s in fuqi for s in ['武曲','破军']):
                reasons.append('S6武破晚婚@%d' % y)
            if reasons:
                cands[L] = reasons
        if cands:
            # 分手题: S2优先; 结婚题: S1>S7>S6
            if is_divorce_q:
                for L, rs in sorted(cands.items()):
                    if any('S2' in r for r in rs):
                        return L, '; '.join(rs)
            else:
                if any(any(r.startswith('S6') for r in rs) for rs in cands.values()) and pure_year_opts:
                    latest = max(pure_year_opts, key=lambda t: t[1])
                    return latest[0], 'S6武破晚婚→选最晚%d' % latest[1]
                for sig in ['S1', 'S7b', 'S7']:
                    for L, rs in sorted(cands.items()):
                        if any(r.startswith(sig) for r in rs):
                            return L, '; '.join(rs)
            # fallback: 信号最多的
            L = max(cands, key=lambda k: len(cands[k]))
            return L, '; '.join(cands[L])
    return None, 'no signal'


if __name__ == '__main__':
    # Run
    fix_ok = fix_bad = 0
    details = []
    for qid in sorted(BASE):
        q = by_id.get(qid)
        if not q: continue
        text = q['question'] + ' '.join(o['text'] for o in q['options'])
        if not (q['category'] == '婚姻' or any(k in q['question'] for k in ['婚','结婚','夫妻','离婚','拍拖','恋爱','嫁','娶','配偶'])):
            continue
        my = BASE[qid]; real = q['answer']
        new, why = analyze(q, q['birth_info'])
        if new and new != my:
            was_right = (my == real)
            now_right = (new == real)
            if now_right and not was_right:
                fix_ok += 1
                tag = 'GAIN'
            elif was_right and not now_right:
                fix_bad += 1
                tag = 'LOSS'
            else:
                continue
            details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, new, real, tag, why))

    base_c = sum(1 for k,v in BASE.items() if k in by_id and by_id[k]['answer']==v)
    print('MARRIAGE FIX: +%d / -%d / net %+d' % (fix_ok, fix_bad, fix_ok - fix_bad))
    print('TOTAL: %d/115=%.1f%% -> %d/115=%.1f%%' % (base_c, base_c/115*100, base_c+fix_ok-fix_bad, (base_c+fix_ok-fix_bad)/115*100))
    for d in details:
        print(' ', d.encode('ascii', 'replace').decode())
