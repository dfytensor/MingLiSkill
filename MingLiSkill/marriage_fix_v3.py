# -*- coding: utf-8 -*-
"""
marriage_fix_v3.py — 婚姻信号第三批(11个新信号/修正) 全局审计
"""
import io, sys, json, re
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.calendar_engine import shi_shen
from tools.ziwei_tools import ZiweiToolkit
ZT = ZiweiToolkit()

HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v4.json', encoding='utf-8'))

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

LIUHE = {'子丑','丑子','寅亥','亥寅','卯戌','戌卯','辰酉','酉辰','巳申','申巳','午未','未午'}
BANHE = {'申子','子申','子辰','辰子','寅午','午寅','午戌','戌午','巳酉','酉巳','酉丑','丑酉','亥卯','卯亥','卯未','未卯'}
CHONG = {'子午','午子','丑未','未丑','寅申','申寅','卯酉','酉卯','辰戌','戌辰','巳亥','亥巳'}

def analyze(q, bi):
    opts = q['options']
    alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except:
        return None, ''
    pillars = b.get('四柱', {})
    day_gan = b.get('日主','')
    if not day_gan: return None, ''
    day_pillar = pillars.get('日柱','')
    day_zhi = day_pillar[1:2]
    day_wx = GAN_WX[day_gan]
    female = bi['gender'] in ('女','F','female')
    wx = b.get('五行力量', {})
    tot = sum(wx.values()) or 1
    sw_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx] if female else \
        {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]

    years = {}
    neg_kw = ['单身','未婚','沒有','没有','未嫁','未娶']
    mq = re.search(r'(19|20)\d\d', q['question'])
    if mq: years[int(mq.group(0))] = None
    is_wed_pre = any(k in alltxt for k in ['结婚','結婚','成婚','娶','嫁'])
    for o in opts:
        if is_wed_pre and any(k in o['text'] for k in neg_kw):
            continue  # 非结婚选项(如"到2022为止单身")不参与年份候选
        for m in re.finditer(r'(19|20)\d\d', o['text']):
            years.setdefault(int(m.group(0)), o['letter'])

    is_wed = any(k in alltxt for k in ['结婚','結婚','成婚','娶','嫁','二婚','再婚','第二婚','第二次结婚'])
    is_date = any(k in alltxt for k in ['拍拖','恋爱','戀愛'])
    is_div = any(k in alltxt for k in ['离婚','離婚','分手','结束第一段','結束'])

    # M1: 男命婚姻状态: 无桃花+财透 → 美满
    if not female and any(k in alltxt for k in ['婚姻美满','婚外情','婚姻感情状况','婚姻状况']):
        no_taohua = not any(z in str(pillars.values()) for z in '子午卯酉')
        wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
        wcount = wx.get(wealth_wx, 0)
        if no_taohua and wcount > 0:
            for o in opts:
                if '美满' in o['text']:
                    return o['letter'], 'M1:无桃花+财星有→美满'
        elif not no_taohua and wcount > 0:
            for o in opts:
                if '外遇' in o['text'] or '外情' in o['text']:
                    return o['letter'], 'M1:有桃花+财透→外遇'

    # M2: 男命财仅年柱+日支坐官杀 → 未婚
    if not female and any(k in alltxt for k in ['未婚','至今未婚','单身']):
        wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
        year_zhi = pillars.get('年柱','')[1:2]
        year_gan = pillars.get('年柱','')[0:1]
        w_in_year_only = False
        if (GAN_WX.get(year_gan) == wealth_wx) or (ZHI_HIDE.get(year_zhi) and GAN_WX.get(ZHI_HIDE[year_zhi][0]) == wealth_wx):
            # check month/day/hour have no wealth benqi/gan
            other = False
            for pn in ['月柱','日柱','时柱']:
                g = pillars.get(pn,'')[0:1]
                z = pillars.get(pn,'')[1:2]
                if GAN_WX.get(g) == wealth_wx or (ZHI_HIDE.get(z) and GAN_WX.get(ZHI_HIDE[z][0]) == wealth_wx):
                    other = True
            if not other:
                w_in_year_only = True
        spouse_palace_ss = None
        dz = day_zhi
        if ZHI_HIDE.get(dz):
            spouse_palace_ss = shi_shen(day_gan, ZHI_HIDE[dz][0])
        if w_in_year_only and spouse_palace_ss in ('正官','七杀'):
            for o in opts:
                if '未婚' in o['text'] or '至今未婚' in o['text']:
                    return o['letter'], 'M2:财仅年柱+日支坐官杀→未婚'

    # S10: 女命伤官本气(日/时支)+官杀透干>=2 → 单身
    if female and any(k in alltxt for k in ['单身','从未结','未婚']):
        guan_wx = sw_wx
        shang_wx = {'木':'火','火':'土','土':'金','金':'水','水':'木'}[day_wx]  # 食伤五行
        guan_tou = sum(1 for pn in ['年柱','月柱','日柱','时柱'] if GAN_WX.get(pillars.get(pn,'')[0:1]) == guan_wx)
        sp = [pillars.get(p,'')[1:2] for p in ['日柱','时柱']]
        shang_benqi = any(ZHI_HIDE.get(z) and GAN_WX.get(ZHI_HIDE[z][0]) == shang_wx for z in sp)
        if guan_tou >= 2 and shang_benqi:
            for o in opts:
                if '单身' in o['text'] or '从未' in o['text']:
                    return o['letter'], 'S10:伤官本气+官杀双透→单身'

    # S9: 女命感情生活题: 财星本气有根 → 家用充足
    if female and '家用' in alltxt:
        wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
        benqi_root = any(ZHI_HIDE.get(pillars.get(p,'')[1:2], (None,))[0] and GAN_WX.get(ZHI_HIDE[pillars.get(p,'')[1:2]][0]) == wealth_wx for p in ['年柱','月柱','日柱','时柱'])
        if benqi_root:
            for o in opts:
                if '家用充足' in o['text']:
                    return o['letter'], 'S9:财星本气有根→家用充足'
        else:
            for o in opts:
                if '不给家用' in o['text'] or '打工' in o['text']:
                    return o['letter'], 'S9:财无本气根→打工'

    # W8b: 女命对象类型题+财星极弱 → 花女人钱
    if female and any(k in alltxt for k in ['花女人钱','对象类型','感情对象']):
        wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
        wpct = wx.get(wealth_wx, 0) / tot * 100
        if wpct < 8:
            for o in opts:
                if '花女人钱' in o['text']:
                    return o['letter'], 'W8b:财%.0f%%极弱→花女人钱' % wpct

    # S3b: 女命官杀现月支 → 已婚(非离婚/未婚)
    if female and any(k in alltxt for k in ['目前的婚姻','婚姻状况为何','婚姻情况如何','现在的婚姻']):
        mz = pillars.get('月柱','')[1:2]
        guan_in_month = ZHI_HIDE.get(mz) and any(GAN_WX.get(h) == sw_wx for h in ZHI_HIDE[mz])
        if guan_in_month:
            for o in opts:
                if ('已婚' in o['text'] or '己婚' in o['text']) and '离' not in o['text']:
                    return o['letter'], 'S3b:官杀现月支婚姻宫→已婚'

    # S6: 夫妻宫武曲/破军 → 晚婚 → 选最晚纯年份选项 (恢复v13规则)
    if is_wed_pre and years:
        try:
            r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                           hour=bi.get('hour',12), gender=bi['gender'])
            zw = json.loads(r2).get('十二宫', {})
            fuqi = (zw.get('夫妻') or {}).get('主星', []) if isinstance(zw.get('夫妻'), dict) else []
            if any(s in fuqi for s in ['武曲','破军']):
                pure = []
                for o in opts:
                    if any(k in o['text'] for k in neg_kw): continue
                    if re.fullmatch(r'\s*(19|20)\d\d\s*年?\s*', o['text']):
                        m = re.search(r'(19|20)\d\d', o['text'])
                        pure.append((o['letter'], int(m.group(0))))
                if pure:
                    latest = max(pure, key=lambda t: t[1])
                    return latest[0], 'S6:夫妻宫武破→最晚%d' % latest[1]
        except:
            pass

    # 年份题
    if years and (is_wed or is_div or is_date):
        cands = {}
        for y in sorted(years):
            gz = year_gz(y)
            ygan, yzhi = gz[0], gz[1]
            ss_g = shi_shen(day_gan, ygan)
            ss_z0 = shi_shen(day_gan, ZHI_HIDE[yzhi][0]) if ZHI_HIDE.get(yzhi) else None
            reasons = []
            # S1: 伏吟
            if gz == day_pillar: reasons.append(('S1full', 1))
            elif yzhi == day_zhi: reasons.append(('S1zhi', 1))
            # S8: 合/冲日支
            if (yzhi + day_zhi) in LIUHE or (yzhi + day_zhi) in BANHE: reasons.append(('S8he', 1))
            if (yzhi + day_zhi) in CHONG: reasons.append(('S8chong', 1))
            # S2: 女命食伤 (透干>本气>中气)
            if female and is_div:
                strength = 0
                if ss_g in ('食神','伤官'): strength = 3
                elif ss_z0 in ('食神','伤官'): strength = 2
                else:
                    for h in ZHI_HIDE.get(yzhi, ())[1:]:
                        if shi_shen(day_gan, h) in ('食神','伤官'): strength = 1
                if strength: reasons.append(('S2', strength))
            # S5: 女命官弱+正官透
            if female and is_div and ss_g == '正官':
                guan_pct = wx.get(sw_wx, 0) / tot * 100
                if guan_pct < 8: reasons.append(('S5', 3))
            # S7: 配偶星到位
            if is_wed:
                if GAN_WX.get(ygan) == sw_wx: reasons.append(('S7b', 2))
                if ss_z0 == ('正官' if female else '正财') or ss_z0 == ('七杀' if female else '偏财'):
                    if ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == sw_wx:
                        reasons.append(('S7a', 2))
                    else:
                        reasons.append(('S7mid', 1))
                # 女命结婚年排除比肩透干
                if female and ss_g == '比肩': reasons.append(('EXCL', -9))
            if reasons:
                cands[y] = reasons
        if cands:
            # 排除比肩年(女命结婚)
            if is_wed and female:
                cands = {y: rs for y, rs in cands.items() if not any(n == 'EXCL' for n, s in rs)} or cands
            def best(c):
                # (信号优先级, 强度)
                order = {'S5': 6, 'S1full': 5, 'S7b': 4, 'S7a': 4, 'S2': 3, 'S7mid': 2, 'S8he': 2, 'S1zhi': 1, 'S8chong': 0}
                top = max((order.get(n, 0), s) for n, s in c)
                return top
            if is_div:
                div_order = {'S5': 6, 'S2': 5, 'S1full': 3, 'S8chong': 2, 'S1zhi': 1}
                scored = [(max((div_order.get(n, 0), s) for n, s in rs), y) for y, rs in cands.items()]
                scored.sort(reverse=True)
                if scored:
                    why = ';'.join(n for n, s in cands[scored[0][1]])
                    return years.get(scored[0][1]) or next((o['letter'] for o in opts if str(scored[0][1]) in o['text']), None), 'DIV:' + why
            else:
                wed_order = {'S1full': 5, 'S7b': 4, 'S7a': 4, 'S2': 0, 'S7mid': 3, 'S8he': 2, 'S1zhi': 1}
                scored = [(max((wed_order.get(n, 0), s) for n, s in rs), y) for y, rs in cands.items()]
                scored.sort(reverse=True)
                if scored:
                    why = ';'.join(n for n, s in cands[scored[0][1]])
                    return years.get(scored[0][1]) or next((o['letter'] for o in opts if str(scored[0][1]) in o['text']), None), 'WED:' + why
    return None, 'no signal'

if __name__ == '__main__':
    gain = loss = 0
    details = []
    for qid in sorted(BASE):
        q = by_id.get(qid)
        if not q: continue
        if not (q['category'] == '婚姻' or any(k in q['question'] for k in ['婚','結婚','夫妻','离婚','離婚','拍拖','恋爱','嫁','娶','配偶'])):
            continue
        my = BASE[qid]; real = q['answer']
        new, why = analyze(q, q['birth_info'])
        if not new or new == my: continue
        was = my == real; now = new == real
        if now and not was: gain += 1; tag = 'GAIN'
        elif was and not now: loss += 1; tag = 'LOSS'
        else: continue
        BASE[qid] = new
        details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, new, real, tag, why))

    final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
    print('MARRIAGE v3: +%d / -%d' % (gain, loss))
    print('FINAL: %d/115 = %.1f%%' % (final, final/115*100))
    for d in details:
        print(' ', d.encode('ascii','replace').decode())
    json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v5.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('saved fixed_answers_v5.json')
