# -*- coding: utf-8 -*-
"""
reverse_match.py — 逆向匹配法（全新方法）
对每个选项反推"命盘应有什么特征"，与实际命盘匹配打分。
不依赖规则记忆，纯特征对比。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.shensha import natal_shensha, year_shensha
from tools.calendar_engine import year_ganzhi, ZHI_CANG_GAN, WUXING_GAN, shi_shen

HTK = HybridMingliToolkit()
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'


def extract_chart_profile(chart):
    """提取命盘的完整特征向量。"""
    b = chart.get('bazi', {})
    z = chart.get('ziwei', {})
    pillars = b.get('四柱', {})
    wx = b.get('五行力量', {})
    ss = b.get('十神', {})
    total = sum(wx.values()) or 1
    
    profile = {
        # 日主
        'day_gan': b.get('日主', ''),
        'day_wx': b.get('日主五行', ''),
        'strong': b.get('日主强弱', '') == '身强',
        'gender': chart.get('gender', ''),
        # 十神透干
        'tg_shishen': set(v for k, v in ss.items() if '天干' in k),
        # 十神全表
        'all_shishen': set(ss.values()),
        # 十神强度
        'ss_count': {name: sum(1 for v in ss.values() if v == name) for name in set(ss.values())},
        # 五行占比
        'wx_pct': {w: c/total for w, c in wx.items()},
        # 缺失五行
        'missing_wx': [w for w, c in wx.items() if c == 0],
        # 极旺五行(>40%)
        'extreme_wx': [w for w, c in wx.items() if c/total > 0.4],
        # 空亡
        'kong_wang': b.get('空亡', []),
        # 四柱地支
        'zhis': [pillars.get(k, '')[1:2] for k in ('年柱', '月柱', '日柱', '时柱')],
        # 四柱天干
        'gans': [pillars.get(k, '')[0:1] for k in ('年柱', '月柱', '日柱', '时柱')],
        # 配偶宫(日支)
        'spouse_palace': pillars.get('日柱', '')[1:2],
        # 配偶宫藏干十神
        'spouse_hidden_ss': ss.get('日柱地支本气', ''),
        # 紫微命宫
        'zw_ming': z.get('命宫主星', []),
        'zw_guanlu': z.get('官禄宫主星', []),
        'zw_fuqi': z.get('夫妻宫主星', []),
        'zw_caibo': z.get('财帛宫主星', []),
        'zw_jie': z.get('疾厄宫主星', []),
        'zw_zinv': z.get('子女宫主星', []),
        # 神煞
        'shensha': set(),
        # 流年
        'liunian': chart.get('liunian', {}).get('年份流年对比', []),
    }
    
    # 神煞
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    natal = natal_shensha(yz, dz, b.get('日主', ''))
    profile['shensha'] = set(natal['positions'].values())
    
    # 女命/男命特定
    female = chart.get('gender', '') in ('女', 'F', 'female')
    profile['female'] = female
    if female:
        profile['spouse_star'] = '官杀'  # 官杀=丈夫
        profile['spresent'] = [v for v in ss.values() if v in ('正官', '七杀')]
        profile['children_star'] = '食伤'
        profile['cpresent'] = [v for v in ss.values() if v in ('食神', '伤官')]
    else:
        profile['spouse_star'] = '财星'  # 财=妻子
        profile['spresent'] = [v for v in ss.values() if v in ('正财', '偏财')]
        profile['children_star'] = '官杀'
        profile['cpresent'] = [v for v in ss.values() if v in ('正官', '七杀')]
    
    return profile


def match_score(profile, expectations):
    """计算命盘与假设条件的匹配度。
    expectations: [('需要', 特征描述), ('不能有', 特征描述)]
    每满足一个'需要' +2, 每违反一个'不能有' -2"""
    score = 0.0
    details = []
    for req_type, desc in expectations:
        if req_type == '需要':
            if desc in profile.get('tg_shishen', set()) or desc in profile.get('all_shishen', set()):
                score += 2
                details.append('+%s(有)' % desc)
            elif desc in str(profile.get('wx_pct', {})):
                score += 1
                details.append('+%s(五行)' % desc)
            elif desc in str(profile.get('zw_ming', [])) or desc in str(profile.get('zw_fuqi', [])):
                score += 1.5
                details.append('+%s(紫微)' % desc)
            elif desc in str(profile.get('shensha', set())):
                score += 1.5
                details.append('+%s(神煞)' % desc)
            else:
                details.append('-%s(无)' % desc)
        elif req_type == '不能有':
            if desc in profile.get('tg_shishen', set()) or desc in profile.get('all_shishen', set()):
                score -= 2
                details.append('-%s(有但不应有)' % desc)
            elif desc in str(profile.get('missing_wx', [])):
                score += 1
                details.append('+%s(确实缺)' % desc)
            else:
                details.append('?%s' % desc)
        elif req_type == '五行':
            # desc = '木>0.2' or '火=0'
            pass
    
    return score, details


def reverse_match(question, options, chart, category):
    """逆向匹配：每个选项反推命盘特征，与实际命盘匹配。"""
    profile = extract_chart_profile(chart)
    
    # 选项类型判断和期望特征定义
    scores = {}
    all_details = {}
    
    for o in question.get('options', []):
        letter = o.get('letter', '?')
        txt = o.get('text', '')
        
        expectations = []
        female = profile['female']
        
        # 婚姻类
        if any(t in txt for t in ['已婚', '结婚', '娶', '嫁']):
            expectations.append(('需要', '正财' if not female else '正官'))
            expectations.append(('不能有', '伤官'))  # 伤官克官=婚不顺
        if any(t in txt for t in ['离婚', '离异', '分手']):
            expectations.append(('不能有', '正官' if female else '正财'))
            expectations.append(('需要', '伤官'))
        if any(t in txt for t in ['未婚', '单身', '光棍', '独身']):
            expectations.append(('不能有', '正官' if female else '正财'))
        if any(t in txt for t in ['外遇', '情人', '脚踏', '桃花']):
            expectations.append(('需要', '偏财' if not female else '七杀'))
        
        # 子女类
        if any(t in txt for t in ['孩子', '子女', '儿子', '女儿', '生']):
            expectations.append(('需要', '食神'))
            expectations.append(('需要', '伤官'))
        if any(t in txt for t in ['无子', '流产', '难产']):
            expectations.append(('不能有', '食神'))
        
        # 财富类
        if any(t in txt for t in ['富', '有钱', '身家', '老板']):
            expectations.append(('需要', '正财'))
            expectations.append(('需要', '偏财'))
        if any(t in txt for t in ['贫', '穷', '负债', '欠']):
            expectations.append(('不能有', '正财'))
        
        # 事业类
        if any(t in txt for t in ['公职', '公务员', '政府', '官员']):
            expectations.append(('需要', '正官'))
        if any(t in txt for t in ['老板', '创业', '自己']):
            expectations.append(('需要', '偏财'))
            expectations.append(('不能有', '正官'))
        if any(t in txt for t in ['技术', '电脑', '工程']):
            expectations.append(('需要', '食神'))
            expectations.append(('需要', '伤官'))
        
        # 健康类
        if category == '健康' or any(t in txt for t in ['病', '伤', '手术', '癌']):
            # 五行缺失/极旺对应器官
            for w, pct in profile['wx_pct'].items():
                organs = {'木': '肝胆', '火': '心脏', '土': '脾胃', '金': '肺', '水': '肾脑'}.get(w, '')
                if pct == 0 and organs and organs[0] in txt:
                    expectations.append(('五行', '%s=0' % w))
                if pct > 0.4 and organs and organs[0] in txt:
                    expectations.append(('五行', '%s>0.4' % w))
        
        # 性格类
        if any(t in txt for t in ['聪明', '智', '慧']):
            expectations.append(('需要', '食神'))
            expectations.append(('需要', '伤官'))
        if any(t in txt for t in ['暴躁', '急', '冲']):
            expectations.append(('需要', '七杀'))
        if any(t in txt for t in ['温和', '柔', '善']):
            expectations.append(('需要', '正印'))
        if any(t in txt for t in ['固执', '保守']):
            expectations.append(('需要', '比肩'))
        
        # 学业类
        if any(t in txt for t in ['大学', '博士', '硕士', '学历高']):
            expectations.append(('需要', '正印'))
            expectations.append(('需要', '偏印'))
        if any(t in txt for t in ['文盲', '辍学', '学历低']):
            expectations.append(('不能有', '正印'))
        
        # 计算匹配度
        if expectations:
            score, details = match_score(profile, expectations)
            scores[letter] = score
            all_details[letter] = details
        else:
            scores[letter] = 0
            all_details[letter] = ['无特征匹配']
    
    return scores, all_details


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
        
        scores, details = reverse_match(q, q.get('options', []), chart, cat)
        best = max(scores, key=lambda L: scores[L]) if scores else 'A'
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(cat, [0, 0])
        cat_stats[cat][0] += ok
        cat_stats[cat][1] += 1
        detail.append('%s %-4s %s->%s %s | %s' % (q['id'], cat, best, real, 'OK' if ok else 'X', json.dumps(scores)))
    
    lines = ['=== REVERSE MATCH ENGINE (NEW METHOD) ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct/total*100))
    lines.append('vs hybrid: 64/160 = 40.0%')
    lines.append('')
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d (%.0f%%)' % (cat, s[0], s[1], s[0]/max(s[1],1)*100))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\reverse_match_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('REVERSE MATCH: %d/%d = %.1f%%' % (correct, total, correct/total*100))


if __name__ == '__main__':
    main()
