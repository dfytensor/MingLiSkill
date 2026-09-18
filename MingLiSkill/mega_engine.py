# -*- coding: utf-8 -*-
"""
mega_engine.py — 全工具全调用最终引擎
每个问题调用所有相关工具，输出汇总信号，选最高分选项。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit
from tools.bazi_tools import BaziToolkit
from tools.shensha import natal_shensha, year_shensha
from tools.calendar_engine import year_ganzhi, shi_shen, WUXING_GAN
from extra_tools import auto_yongshen
from knowledge_base import query_kb
from ziwei_interpret import query_ziwei_interpret

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()
BT = BaziToolkit()

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'


def full_tool_analysis(bi, category, question, options):
    """调用所有工具，返回每个选项的综合分数。"""
    gender = bi['gender']
    year, month, day = bi['year'], bi['month'], bi['day']
    hour = bi.get('hour', 12)

    # ===== TOOL 1: HybridMingliToolkit.analyze_question =====
    try:
        r1 = HTK.analyze_question(year=year, month=month, day=day, hour=hour,
                                   gender=gender, category=category, question=question,
                                   options_json=json.dumps(options, ensure_ascii=False))
        chart = json.loads(r1)
    except:
        chart = {}

    b = chart.get('bazi', {})
    z = chart.get('ziwei', {})
    pillars = b.get('四柱', {})
    wx = b.get('五行力量', {})
    ss = b.get('十神', {})
    day_gan = b.get('日主', '')
    day_wx = b.get('日主五行', '')
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    huoyuan = chart.get('huoyuan_analysis', {})
    wealth_tip = chart.get('wealth_analysis', {}).get('财运提示', '')

    # ===== TOOL 2: BaziToolkit 专项分析 =====
    specialty = {}
    try:
        specialty['career'] = json.loads(BT.analyze_career(pillars, gender))
    except: pass
    try:
        specialty['marriage'] = json.loads(BT.analyze_marriage(pillars, gender))
    except: pass
    try:
        specialty['wealth'] = json.loads(BT.analyze_wealth(pillars))
    except: pass
    try:
        specialty['health'] = json.loads(BT.analyze_health(pillars))
    except: pass
    try:
        specialty['guan_sha'] = json.loads(BT.analyze_guan_sha(pillars))
    except: pass
    try:
        specialty['cai_xing'] = json.loads(BT.analyze_cai_xing(pillars))
    except: pass

    # ===== TOOL 3: 流月分析 =====
    liuyue_data = {}
    try:
        r3 = BT.analyze_liuyue(pillars, year, gender)
        liuyue_data = json.loads(r3)
    except: pass

    # ===== TOOL 4: 冲合检查 =====
    chong_he = {}
    try:
        r4 = BT.check_chong_he(pillars)
        chong_he = json.loads(r4)
    except: pass

    # ===== TOOL 5: 神煞 =====
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    natal = natal_shensha(yz, dz, day_gan)
    natal_zhis = [pillars.get(k, '')[-1:] for k in ('年柱','月柱','日柱','时柱')]

    # ===== TOOL 6: ZiweiToolkit 完整排盘 =====
    try:
        r6 = ZT.paipan(year=year, month=month, day=day, hour=hour, gender=gender)
        zw_full = json.loads(r6)
    except:
        zw_full = {}

    zw_palaces = zw_full.get('十二宫', {})
    zw_stars = {}
    for palace_name, palace_data in zw_palaces.items():
        stars = palace_data.get('主星', [])
        if stars:
            zw_stars[palace_name] = stars

    # ===== TOOL 7: ZiweiToolkit 宫位分析 =====
    zw_analysis = {}
    ming_stars = zw_stars.get('命宫', [])
    if ming_stars:
        try:
            zw_analysis['personality'] = json.loads(ZT.analyze_personality(json.dumps(ming_stars)))
        except: pass
        try:
            zw_analysis['palace'] = json.loads(ZT.analyze_palace('命宫', json.dumps(ming_stars)))
        except: pass

    guanlu_stars = zw_stars.get('官禄', [])
    if guanlu_stars:
        try:
            zw_analysis['career'] = json.loads(ZT.analyze_career(json.dumps(guanlu_stars), json.dumps(ming_stars)))
        except: pass

    couple_stars = zw_stars.get('夫妻', [])
    if couple_stars:
        try:
            zw_analysis['marriage'] = json.loads(ZT.analyze_marriage(json.dumps(couple_stars)))
        except: pass

    # ===== TOOL 8: 紫微断语 =====
    try:
        zw_interp = query_ziwei_interpret(zw_stars)
    except:
        zw_interp = []

    # ===== TOOL 9: 知识库 =====
    tg_vals = list(set(v for k, v in ss.items() if k.endswith('天干')))
    kb_feats = {'十神透干': tg_vals}
    if gender in ('女', 'F'):
        kb_feats['女命十神'] = tg_vals
    kb_res = query_kb(kb_feats, top_n=8)

    # ===== TOOL 10: 用神 =====
    ys = auto_yongshen(category, b)

    # ===== TOOL 11: 神煞年份 =====
    opt_years = {}
    for o in options:
        letter = o.get('letter', '?')
        txt = str(o.get('text', ''))
        for yr_str in re.findall(r'(19\d{2}|20\d{2})', txt):
            yr = int(yr_str)
            lgz = year_ganzhi(yr)
            lz = lgz[-1:]
            try:
                sh = year_shensha(yz, dz, lz, natal_zhis)
                if sh:
                    opt_years.setdefault(letter, []).extend(sh)
            except: pass

    # ===== TOOL 12: 流年数据 =====
    liunian = chart.get('liunian') or {}

    # ===== SCORE OPTIONS =====
    option_scores = {}
    option_reasons = {}
    
    for o in options:
        letter = o.get('letter', '?')
        txt = str(o.get('text', ''))
        score = 0.0
        reasons = []

        # S1: Bazi 喜忌
        if yong and yong in txt:
            score += 2; reasons.append('喜用')
        if ji and ji in txt:
            score -= 2; reasons.append('忌神')

        # S2: 五行极端
        tw = sum(wx.values()) or 1
        for w, c in wx.items():
            pct = c / tw
            organ = {'木':'肝胆','火':'心','土':'脾胃','金':'肺','水':'肾脑骨'}.get(w, '')
            if pct == 0 and organ and organ in txt and category == '健康':
                score += 5; reasons.append('缺%s(%s)' % (w, organ))
            if pct > 0.4 and organ and organ in txt and category == '健康':
                score += 3; reasons.append('旺%s(%s)' % (w, organ))

        # S3: BaziToolkit 专项分析
        spec_key = {'事业': 'career', '婚姻': 'marriage', '财运': 'wealth', '健康': 'health'}.get(category)
        if spec_key and spec_key in specialty:
            spec = specialty[spec_key]
            spec_str = json.dumps(spec, ensure_ascii=False)
            # Check if option text matches specialty keywords
            for kw in re.findall(r'[\u4e00-\u9fff]{2,4}', txt):
                if kw in spec_str:
                    score += 1.5

        # S4: ZiweiToolkit 专项分析
        zw_spec_key = {'事业': 'career', '婚姻': 'marriage'}.get(category)
        if zw_spec_key and zw_spec_key in zw_analysis:
            zw_spec = zw_analysis[zw_spec_key]
            zw_str = json.dumps(zw_spec, ensure_ascii=False)
            for kw in re.findall(r'[\u4e00-\u9fff]{2,4}', txt):
                if kw in zw_str:
                    score += 1.5

        # S5: Ziwei 断语
        for desc, src in zw_interp:
            # extract meaningful words from interpretation
            for kw in ['富','贵','管','领导','桃花','婚','艺术','技','医','变','破','寿','孤']:
                if kw in desc and kw in txt:
                    score += 1.5; reasons.append('紫微:%s' % kw)

        # S6: 神煞年份
        if letter in opt_years:
            sh_str = str(opt_years[letter])
            if '红鸾' in sh_str or '天喜' in sh_str:
                if any(t in txt for t in ['结婚','婚','嫁']): score += 6; reasons.append('红鸾天喜')
            if '桃花' in sh_str:
                if any(t in txt for t in ['恋爱','感情','交']): score += 4; reasons.append('桃花')
            if '驿马' in sh_str:
                if any(t in txt for t in ['出国','移民','留学','搬迁']): score += 4; reasons.append('驿马')
            if '三刑' in sh_str:
                if any(t in txt for t in ['官司','牢','手术','伤']): score += 3; reasons.append('三刑')

        # S7: KB 断语
        for _, e in kb_res:
            for kw in e['关键词']:
                try:
                    if re.search(kw, txt): score += 1
                except: pass

        # S8: 身强身弱
        if '身弱' in wealth_tip and any(t in txt for t in ['贫','穷','债']):
            score += 2
        if '身旺' in wealth_tip and any(t in txt for t in ['富','老板']):
            score += 2

        # S9: 流年十神
        yr_match = re.search(r'(19\d{2}|20\d{2})', txt)
        if yr_match:
            yr = int(yr_match.group(1))
            for yi in liunian.get('年份流年对比', []):
                if yi.get('年份') == yr:
                    tags = yi.get('标签', [])
                    if any('喜用' in t for t in tags): score += 2
                    if any('忌神' in t for t in tags): score -= 2
                    gan_ss = yi.get('天干十神', '')
                    ss_themes = {
                        '正财': ['财','收入'], '偏财': ['投资','生意','父'],
                        '正官': ['工作','升职','公职'], '七杀': ['压力','手术','伤'],
                        '正印': ['学','文书','母','证书'], '偏印': ['偏门','玄学'],
                        '食神': ['才华','子女','餐饮'], '伤官': ['创作','口才','叛逆'],
                        '比肩': ['朋友','合作'], '劫财': ['被骗','破财'],
                    }
                    for theme_kw, theme_opts in ss_themes.items():
                        if gan_ss == theme_kw:
                            for topt in theme_opts:
                                if topt in txt: score += 3; reasons.append('流年:%s' % gan_ss)

        # S10: 神煞主题匹配
        natal_str = json.dumps(natal['positions'], ensure_ascii=False)
        for kw in ['红鸾','天喜','桃花','驿马','华盖','文昌']:
            if kw in natal_str and kw in txt:
                score += 2; reasons.append('原局神煞:%s' % kw)

        option_scores[letter] = score
        option_reasons[letter] = reasons

    return option_scores, option_reasons


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)

    correct = total = 0
    detail = []
    cat_stats = {}

    for q in data['questions']:
        bi = q['birth_info']
        cat = q['category']
        try:
            scores, reasons = full_tool_analysis(bi, cat, q['question'], q['options'])
        except Exception as e:
            scores = {}
            reasons = {}

        if scores:
            best = max(scores, key=lambda L: scores[L])
        else:
            best = 'A'
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(cat, [0,0])
        cat_stats[cat][0] += ok
        cat_stats[cat][1] += 1
        detail.append('%s %-4s %s->%s %s' % (q['id'], cat, best, real, 'OK' if ok else 'X'))

    lines = ['=== MEGA ENGINE (ALL TOOLS x ALL FUNCTIONS) ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct/total*100))
    lines.append('vs committed hybrid: 64/160 = 40.0%')
    lines.append('')
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d (%.0f%%)' % (cat, s[0], s[1], s[0]/max(s[1],1)*100))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\mega_engine_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('MEGA ENGINE: %d/%d = %.1f%%' % (correct, total, correct/total*100))


if __name__ == '__main__':
    main()
