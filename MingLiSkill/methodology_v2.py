# -*- coding: utf-8 -*-
"""
methodology_v2.py — 修正后的推理方法论（盲派象法直读 + 十神关系）
替代之前的五行刻板映射规则。
在主 benchmark 160 题上回顾验证。
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.calendar_engine import year_ganzhi, shi_shen, ZHI_CANG_GAN, WUXING_GAN
from tools.shensha import natal_shensha, year_shensha
from collections import Counter

HTK = HybridMingliToolkit()
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'

# ============ 十神→人生主题映射（修正版：关系直读而非五行刻板） ============
SS_DIRECT = {
    '正财': '正妻·稳定收入·务实·薪水',
    '偏财': '父亲·横财·投机·生意·大方',
    '正官': '丈夫(女)·上司·约束·公职·名声',
    '七杀': '情人(女)·压力·竞争·手术·开创·权威',
    '正印': '母亲·学历·文书·房产·传统·保守·中医',
    '偏印': '偏母·玄学·偏门·独特·古怪·创新·宗教',
    '食神': '子女(温和)·口福·艺术·技艺·享受·长寿',
    '伤官': '子女(叛逆)·口才·创新·克官(官非/离婚)·聪明',
    '比肩': '兄弟·朋友·自我·竞争·合伙·固执',
    '劫财': '破财·被骗·争夺·冲动·赌性',
}

# 地支类象（直读）
ZHI_DIRECT = {
    '子': '耳·肾·隐秘·夜·暗·贼·井',
    '丑': '腹·脾胃·牛·矿·金库·牢狱·寺院',
    '寅': '胆·虎·大树·驿马·道路·公门·学校',
    '卯': '肝·兔·床·车·船·门户·手·振动',
    '辰': '皮肤·龙·水库·网络·天罗·医药',
    '巳': '面·蛇·炉冶·道路·文艺·阴火',
    '午': '眼·心·马·文书·信息·大火·血液',
    '未': '脾·羊·林园·酒器·木库·井',
    '申': '大肠·猴·道路·金石·驿马·车辆',
    '酉': '肺·鸡·金银·酒·刀·针·精细',
    '戌': '腿·狗·火库·窑炉·庙宇·刑',
    '亥': '肾·猪·江河·暗水·头·厕所',
}

# 天干类象
GAN_DIRECT = {
    '甲': '头·胆·大树·栋梁·领袖·直',
    '乙': '颈·毛发·花草·藤萝·柔· artistic',
    '丙': '肩·太阳·影视·火·光明·影响力',
    '丁': '心·灯火·文字·香火·文化·思想',
    '戊': '胃·城墙·堤坝·地产·厚重·信',
    '己': '脾·田园·平原·包容·滋养·务实',
    '庚': '大肠·刀剑·矿石·刚硬·变革·义',
    '辛': '肺·珠玉·精细·金融·柔金·秀',
    '壬': '膀胱·江河·流动·智慧·贸易·智',
    '癸': '肾·雨露·暗流·渗透·智谋·静',
}


def extract_features(bazi, ziwei, liunian, gender, category, question, options):
    """提取完整特征用于选项匹配。"""
    b = bazi
    pillars = b.get('四柱', {})
    wx = b.get('五行力量', {})
    ss = b.get('十神', {})
    day_gan = b.get('日主', '')
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    day_wx = b.get('日主五行', '')
    strong = b.get('日主强弱', '') == '身强'
    
    female = gender in ('女', 'F', 'female')
    
    # 十神透干（天干位置的十神）
    tg = {k: v for k, v in ss.items() if '天干' in k}
    tg_names = list(tg.values())
    tg_count = Counter(tg_names)
    
    # 十神全表（含地支藏干）
    all_ss = list(ss.values())
    ss_count = Counter(all_ss)
    
    # 藏干分析
    hidden_stars = []
    for pos in ('年柱', '月柱', '日柱', '时柱'):
        z = pillars.get(pos, '')[1:2]
        if z:
            for g in ZHI_CANG_GAN.get(z, []):
                s = shi_shen(day_gan, g)
                hidden_stars.append(s)
    hidden_count = Counter(hidden_stars)
    
    # 冲合刑
    interactions = []
    zhis = [pillars.get(k, '')[1:2] for k in ('年柱', '月柱', '日柱', '时柱')]
    chong_pairs = [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            a, b_z = zhis[i], zhis[j]
            if (a, b_z) in chong_pairs or (b_z, a) in chong_pairs:
                interactions.append('%s冲%s' % (a, b_z))
    
    # 神煞
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    natal = natal_shensha(yz, dz, day_gan)
    natal_zhis = zhis
    
    # 紫微
    zw = {}
    for k, v in (ziwei or {}).items():
        if k.endswith('主星') and isinstance(v, list):
            zw[k.replace('主星', '')] = v
    
    # 流年
    ln = liunian or {}
    
    return {
        'pillars': pillars, 'wx': wx, 'ss': ss, 'day_gan': day_gan,
        'day_wx': day_wx, 'yong': yong, 'ji': ji, 'strong': strong,
        'female': female, 'tg_names': tg_names, 'tg_count': tg_count,
        'ss_count': ss_count, 'hidden_count': hidden_count,
        'interactions': interactions, 'natal': natal, 'zhis': zhis,
        'zw': zw, 'ln': ln, 'category': category, 'question': question,
    }


ORGAN_MAP = {'木': ['肝胆', '筋', '目'], '火': ['心', '小肠', '血脉'], '土': ['脾胃', '肌肉'],
             '金': ['肺', '大肠', '皮毛'], '水': ['肾', '膀胱', '骨', '耳']}


def score_option(opt_text, opt_letter, features, liunian_data):
    """用修正后的方法论给选项打分。"""
    score = 0.0
    txt = opt_text
    f = features
    
    # ===== 方法论1: 十神直读（非五行刻板） =====
    # 透干十神含义与选项匹配
    for ss_name, cnt in f['tg_count'].items():
        desc = SS_DIRECT.get(ss_name, '')
        themes = SS_DIRECT.get(ss_name, '').split('·')
        for theme in themes:
            if theme and theme in txt:
                # 透干=明面之事，力量大
                score += 2.0 * min(cnt, 3)
    
    # ===== 方法论2: 藏干分析 =====
    for ss_name, cnt in f['hidden_count'].items():
        desc = SS_DIRECT.get(ss_name, '')
        themes = desc.split('·') if desc else []
        for theme in themes:
            if theme and theme in txt:
                # 藏干=暗中之事，力量较小
                score += 0.8 * min(cnt, 2)
    
    # ===== 方法论3: 官杀混杂/伤官克官（女命婚姻） =====
    if f['female']:
        guan = f['ss_count'].get('正官', 0) + f['ss_count'].get('七杀', 0)
        shang = f['ss_count'].get('伤官', 0)
        if guan > 0 and shang > 0:
            if any(t in txt for t in ['离婚', '婚变', '外遇', '情人']):
                score += 3
        if shang >= 2 and guan == 0:
            if any(t in txt for t in ['单身', '未婚', '离婚']):
                score += 2
    
    # ===== 方法论4: 男命比劫夺财 =====
    if not f['female']:
        bijie = f['ss_count'].get('比肩', 0) + f['ss_count'].get('劫财', 0)
        cai = f['ss_count'].get('正财', 0) + f['ss_count'].get('偏财', 0)
        if bijie >= 3 and any(t in txt for t in ['被骗', '破财', '投机']):
            score += 3
        if cai == 0 and bijie >= 2:
            if any(t in txt for t in ['单身', '无妻', '光棍']):
                score += 2
    
    # ===== 方法论5: 冲对应激事件 =====
    for inter in f['interactions']:
        if '冲' in inter:
            # 冲=变动/冲突/意外
            zhi_a = inter.split('冲')[0]
            direct = ZHI_DIRECT.get(zhi_a, '')
            themes = direct.split('·')
            for theme in themes:
                if theme and theme in txt:
                    score += 2
    
    # ===== 方法论6: 神煞应期 =====
    yr_match = re.search(r'(19\d{2}|20\d{2})', txt)
    if yr_match:
        yr = int(yr_match.group(1))
        lgz = year_ganzhi(yr)
        lz = lgz[-1:]
        try:
            sh = year_shensha(f['pillars'].get('年柱','')[-1:], 
                            f['pillars'].get('日柱','')[-1:],
                            lz, f['zhis'])
            sh_str = str(sh)
            if '红鸾' in sh_str or '天喜' in sh_str:
                if any(t in txt for t in ['结婚', '婚', '嫁', '喜']):
                    score += 5
            if '桃花' in sh_str:
                if any(t in txt for t in ['恋爱', '感情', '桃花', '交']):
                    score += 4
            if '驿马' in sh_str:
                if any(t in txt for t in ['出国', '移民', '留学', '搬迁', '到', '旅行']):
                    score += 4
            if '三刑' in sh_str:
                if any(t in txt for t in ['官司', '牢', '手术', '伤', '刀']):
                    score += 3
        except:
            pass
    
    # ===== 方法论7: 流年十神直读 =====
    for yi in (f['ln'] or {}).get('年份流年对比', []):
        yr = yi.get('年份')
        if yr_match and int(yr_match.group(1)) == yr:
            gan_ss = yi.get('天干十神', '')
            direct = SS_DIRECT.get(gan_ss, '')
            themes = direct.split('·') if direct else []
            for theme in themes:
                theme = theme.strip()
                if theme and theme in txt:
                    score += 3
            # 喜忌
            tags = yi.get('标签', [])
            if any('喜用' in t for t in tags):
                score += 1
            if any('忌神' in t for t in tags):
                score -= 1
    
    # ===== 方法论8: 五行极旺/极弱（仅限健康题） =====
    if f['category'] == '健康':
        total = sum(f['wx'].values()) or 1
        for w, c in f['wx'].items():
            pct = c / total
            organs = ORGAN_MAP.get(w, [])
            if pct == 0:
                for organ in organs:
                    if organ in txt:
                        score += 5
            elif pct > 40:
                for organ in organs:
                    if organ in txt:
                        score += 2
    
    # ===== 方法论9: 紫微命宫断语 =====
    ming_stars = f['zw'].get('命宫', [])
    from ziwei_interpret import STAR_NATURE
    for star in ming_stars:
        nature = STAR_NATURE.get(star, '')
        themes = nature.split('、') if nature else []
        for theme in themes:
            if theme and theme in txt:
                score += 1.5
    
    return score


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
            r = HTK.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=cat, question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            chart = json.loads(r)
        except:
            chart = {}
        
        features = extract_features(
            chart.get('bazi', {}), chart.get('ziwei', {}),
            chart.get('liunian', {}), bi['gender'],
            cat, q['question'], q['options'])
        
        # Score each option
        opt_scores = {}
        for o in q.get('options', []):
            letter = o.get('letter', '?')
            txt = o.get('text', '')
            s = score_option(txt, letter, features, chart.get('liunian', {}))
            opt_scores[letter] = s
        
        best = max(opt_scores, key=lambda L: opt_scores[L]) if opt_scores else 'A'
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(cat, [0,0])
        cat_stats[cat][0] += ok
        cat_stats[cat][1] += 1
        detail.append('%s %-4s %s->%s %s' % (q['id'], cat, best, real, 'OK' if ok else 'X'))
    
    lines = ['=== METHODOLOGY V2 (盲派象法直读 + 十神关系) ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct/total*100))
    lines.append('vs v1 committed: 64/160 = 40.0%')
    lines.append('vs human top-20: 51.88%')
    lines.append('')
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d (%.0f%%)' % (cat, s[0], s[1], s[0]/max(s[1],1)*100))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\methodology_v2_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('METHODOLOGY V2: %d/%d = %.1f%%' % (correct, total, correct/total*100))


if __name__ == '__main__':
    main()
