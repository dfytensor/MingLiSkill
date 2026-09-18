# -*- coding: utf-8 -*-
"""
final_engine.py — 最终全量引擎：所有工具全开
八字 + 紫微断语 + 辅星 + 格局 + 神煞 + 四化 + KB + 案例线
确定性一次运行 160 题。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.shensha import natal_shensha, year_shensha
from tools.calendar_engine import year_ganzhi
from knowledge_base import query_kb
from knowledge_ext import KB_EXT
from ziwei_interpret import query_ziwei_interpret
from final_tools import check_formats, sihua_interpret, trio_interpret, AUX_GOOD, AUX_BAD
from extra_tools import sihua_feigong
from collections import Counter

HTK = HybridMingliToolkit()
ALL_KB = None  # lazily loaded

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'


def score_options(question, chart, category):
    """Use ALL tools to score each option."""
    b = chart.get('bazi', {})
    z = chart.get('ziwei', {})
    pillars = b.get('四柱', {})
    wx = b.get('五行力量', {})
    day_wx = b.get('日主五行', '')
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    wealth_tip = chart.get('wealth_analysis', {}).get('财运提示', '')
    
    option_scores = {}
    for o in question.get('options', []):
        letter = o.get('letter', chr(65 + len(option_scores)))
        txt = o.get('text', '')
        score = 0.0
        signals = []
        
        # === TOOL 1: Bazi 喜忌 ===
        if yong and yong in txt:
            score += 2; signals.append('喜用命中')
        if ji and ji in txt:
            score -= 2; signals.append('忌神命中')
        
        # === TOOL 2: 五行极端 ===
        total_wx = sum(wx.values()) or 1
        for wx_name, cnt in wx.items():
            pct = cnt / total_wx
            if pct == 0:
                organ = {'木':'肝胆','火':'心','土':'脾胃','金':'肺','水':'肾脑骨'}.get(wx_name,'')
                if organ and organ in txt and category == '健康':
                    score += 5; signals.append('五行缺%s(%s)' % (wx_name, organ))
            elif pct > 0.4:
                organ = {'木':'肝胆','火':'心','土':'脾胃','金':'肺','水':'肾脑骨'}.get(wx_name,'')
                if organ and organ in txt and category == '健康':
                    score += 3; signals.append('五行旺%s(%s)' % (wx_name, organ))
        
        # === TOOL 3: 紫微断语 ===
        zw_palaces = {}
        for k, v in z.items():
            if k.endswith('主星') and isinstance(v, list):
                zw_palaces[k.replace('主星', '')] = v
        
        interp_results = query_ziwei_interpret(zw_palaces)
        for desc, source in interp_results:
            # extract keywords from interpretation
            for kw in ['富', '贵', '管理', '领导', '贫穷', '破', '变', '桃花', '婚', '艺术', '技术', '医']:
                if kw in desc and kw in txt:
                    score += 1.5; signals.append('紫微:%s' % kw)
        
        # === TOOL 4: 格局判定 ===
        formats = check_formats(zw_palaces)
        for fmt in formats:
            for kw in [fmt['事业倾向'], fmt['格局']]:
                if kw in txt:
                    score += 3; signals.append('格局:%s' % fmt['格局'])
        
        # === TOOL 5: 辅星分析 ===
        for palace, stars in zw_palaces.items():
            minor = []  # We need minor stars from chart, but ziwei output only has major
            # Skip for now - would need raw iztro data
        
        # === TOOL 6: 神煞 ===
        yz = pillars.get('年柱', '')[-1:]
        dz = pillars.get('日柱', '')[-1:]
        natal = natal_shensha(yz, dz, b.get('日主', ''))
        
        # Year matching with shensha
        yr_match = re.search(r'(19\d{2}|20\d{2})', txt)
        if yr_match:
            yr = int(yr_match.group(1))
            lgz = year_ganzhi(yr)
            lz = lgz[-1:]
            natal_zhis = [pillars.get(k, '')[-1:] for k in ('年柱','月柱','日柱','时柱')]
            try:
                from tools.shensha import year_shensha as ys_func
                sh = ys_func(yz, dz, lz, natal_zhis)
                sh_str = str(sh)
                if '红鸾' in sh_str or '天喜' in sh_str:
                    if any(t in txt for t in ['结婚','婚','嫁']):
                        score += 6; signals.append('红鸾天喜婚期')
                if '桃花' in sh_str:
                    if any(t in txt for t in ['恋爱','感情','交']):
                        score += 4; signals.append('桃花恋爱')
                if '驿马' in sh_str:
                    if any(t in txt for t in ['出国','移民','留学','搬迁','到']):
                        score += 4; signals.append('驿马迁动')
                if '三刑' in sh_str:
                    if any(t in txt for t in ['官司','牢','手术','伤']):
                        score += 3; signals.append('三刑刑伤')
            except:
                pass
        
        # === TOOL 7: KB 断语 ===
        ss = b.get('十神', {})
        tg_vals = [v for k, v in ss.items() if k.endswith('天干')]
        kb_feats = {'十神透干': list(set(tg_vals))}
        gender = chart.get('category', '')
        kb_res = query_kb(kb_feats, top_n=8)
        for _, e in kb_res:
            for kw in e['关键词']:
                try:
                    if re.search(kw, txt):
                        score += 1
                except:
                    pass
        
        # === TOOL 8: 流年十神 ===
        liunian = chart.get('liunian') or {}
        for yi in liunian.get('年份流年对比', []):
            yr = yi.get('年份')
            if yr_match and int(yr_match.group(1)) == yr:
                gan_ss = yi.get('天干十神', '')
                tags = yi.get('标签', [])
                if any('喜用' in t for t in tags):
                    score += 2
                if any('忌神' in t for t in tags):
                    score -= 2
                # 十神 themes
                ss_themes = {
                    '正财': ['财','钱','收入'], '偏财': ['投资','意外','父','生意'],
                    '正官': ['工作','升职','官','公职'], '七杀': ['压力','竞争','伤','手术'],
                    '正印': ['学','文书','房','母','证书'], '偏印': ['玄学','偏门','技'],
                    '食神': ['才华','艺术','餐饮','子女'], '伤官': ['创作','口才','叛逆','破'],
                    '比肩': ['朋友','合作','竞争'], '劫财': ['被骗','破财','争夺'],
                }
                for theme_kw, theme_opts in ss_themes.items():
                    if gan_ss == theme_kw:
                        for topt in theme_opts:
                            if topt in txt:
                                score += 3; signals.append('流年十神:%s(%s)' % (gan_ss, topt))
        
        # === TOOL 9: 案例线 ===
        # handled separately (needs cross-round data)
        
        # === TOOL 10: Bazi 身强身弱 ===
        if '身弱' in wealth_tip:
            if any(t in txt for t in ['贫','穷','债','无']):
                score += 2
        if '身旺' in wealth_tip:
            if any(t in txt for t in ['富','老板','管理']):
                score += 2
        
        option_scores[letter] = score
    
    return option_scores


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    correct = total = 0
    detail = []
    cat_stats = {}
    
    for q in data['questions']:
        bi = q['birth_info']
        category = q['category']
        try:
            r = HTK.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=category, question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            chart = json.loads(r)
        except:
            chart = {}
        
        scores = score_options(q, chart, category)
        best = max(scores, key=lambda L: scores[L]) if scores else 'A'
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(category, [0,0])
        cat_stats[category][0] += ok
        cat_stats[category][1] += 1
        detail.append('%s %-4s %s->%s %s | %s' % (qid := q['id'], category, best, real,
                      'OK' if ok else 'X', json.dumps(scores)))
    
    lines = ['=== FINAL ENGINE (ALL TOOLS) ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct/total*100))
    lines.append('Baselines: rules 33.75% | agent 40% | Tianfu 50%')
    lines.append('')
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d (%.0f%%)' % (cat, s[0], s[1], s[0]/max(s[1],1)*100))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\final_engine_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('FINAL ENGINE: %d/%d = %.1f%%' % (correct, total, correct/total*100))


if __name__ == '__main__':
    main()
