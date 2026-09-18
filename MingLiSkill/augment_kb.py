# -*- coding: utf-8 -*-
"""Generate KB-augmented digest for a round: per-question chart features -> KB hits."""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from knowledge_base import query_kb, format_kb_results

PREFIX = sys.argv[1] if len(sys.argv) > 1 else 'hybrid9'
qs = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s_charts.json' % PREFIX, encoding='utf-8'))

lines = []
for q in qs:
    d = q['chart_data']
    b = d.get('bazi', {})
    gender = q['birth_info'].get('gender', '男')
    ss_map = b.get('十神', {})
    # 仅天干透出才算触发（收紧KB匹配）
    shishen_set = sorted(set(v for k, v in ss_map.items() if k.endswith('天干')))
    tiangan_ss = [v for k, v in ss_map.items() if k.endswith('天干')]
    female = gender in ('女', 'F', 'female')
    features = {'十神': shishen_set, '神煞': [], '结构': [], '五行': [], '宫位': [],
                '流年': [], '力量': []}
    if female:
        features['女命十神'] = tiangan_ss
        if '伤官' in tiangan_ss:
            features['女命十神'] = features['女命十神'] + ['伤官透干']
        ss_vals = list(ss_map.values())
        if '正官' in ss_vals and '七杀' in ss_vals:
            features['女命十神'].append('官杀混杂')
    else:
        features['男命十神'] = tiangan_ss
        if '正财' in tiangan_ss and '偏财' in tiangan_ss:
            features['男命十神'].append('正偏财混杂')
    # 力量
    wa = d.get('wealth_analysis', {})
    tip = wa.get('财运提示', '')
    if '身弱' in tip:
        features['力量'].append('财多身弱')
    if '身旺' in tip:
        features['力量'].append('身旺任财')
    # 五行最弱
    ha = d.get('health_analysis', {})
    if ha.get('最弱五行'):
        features['五行'].append('最弱五行')
    # 空亡 vs 配偶宫
    kong = b.get('空亡', [])
    day_zhi = b.get('四柱', {}).get('日柱', '')[-1:]
    if day_zhi in kong:
        features['宫位'].append('配偶宫空亡')
    if ss_map.get('日柱地支本气') == '伤官' and female:
        features['宫位'].append('配偶宫坐伤官(女)')
    # 年柱宫位
    if ss_map.get('年柱地支本气') == '正官' or ss_map.get('年柱天干') == '正官':
        features['宫位'].append('年柱正官')
    if ss_map.get('年柱天干') in ('正财', '偏财') or ss_map.get('年柱地支本气') in ('正财', '偏财'):
        features['宫位'].append('年柱财星')
    # 财多坏印
    wx = b.get('五行力量', {})
    day_wx = b.get('日主五行', '')
    yin_wx = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}.get(day_wx)
    cai_wx = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}.get(day_wx)
    if yin_wx and cai_wx and wx.get(cai_wx, 0) > 2.5 and wx.get(yin_wx, 9) < 1.5:
        features['结构'].append('财多坏印')
    # 流年特征 + 神煞
    ln = d.get('liunian') or {}
    for yi in ln.get('年份流年对比', []):
        gan_ss = yi.get('天干十神', '')
        if gan_ss:
            features['流年'].append(gan_ss + '透干')
        for t in yi.get('标签', []):
            if '神煞:' in t:
                name = t.split('神煞:')[1].split('(')[0]
                features['神煞'].append(name)
            if '三刑' in t:
                features['结构'].append('三刑')
    res = query_kb(features, top_n=5)
    lines.append('### Q%d %s [%s] KB=%s' % (q['idx'], q['id'], q['category'],
                                            ' | '.join(format_kb_results(res)) if res else '-'))

with open(r'E:\ming_li_skill\MingLiSkill\%s_kbcontext.txt' % PREFIX, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('ok')
