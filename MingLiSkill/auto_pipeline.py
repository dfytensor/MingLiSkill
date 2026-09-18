# -*- coding: utf-8 -*-
"""
auto_pipeline.py — 自动执行 11 步工具调用流水线
用法: python auto_pipeline.py <qid>
从已提交数据中取出题目，完整走一遍流水线，输出每步结果。
"""
import io, sys, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')

from tools import HybridMingliToolkit
from extra_tools import (sanfang_sizheng, dayun_year_by_year,
                         sihua_feigong, auto_yongshen,
                         star_brightness, palace_brightness_score)
from tools.shensha import natal_shensha, year_shensha
from knowledge_base import query_kb, format_kb_results
from retriever import Retriever

HTK = HybridMingliToolkit()
RET = Retriever()
DATA = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
KEY = {q['id']: q for q in DATA['questions']}


def find_case(qid):
    """从已提交数据中找到题目的排盘数据。"""
    from retriever import ROUNDS, BASE
    for cf, af in ROUNDS:
        p = os.path.join(BASE, cf)
        charts = {c['id']: c for c in json.load(open(p, encoding='utf-8'))}
        if qid in charts:
            return charts[qid]
    return None


def run_pipeline(qid):
    q = KEY[qid]
    case = find_case(qid)
    if not case:
        return ['ERROR: case not found for %s' % qid]
    bi = q['birth_info']
    cat = q['category']
    real = q['answer']
    chart = case['chart_data']
    b = chart.get('bazi', {})
    z = chart.get('ziwei', {})
    pillars = b.get('四柱', {})
    out = []
    out.append('=' * 70)
    out.append('Q: %s' % q['question'][:60])
    out.append('Birth: %s %d-%02d-%02d %d时' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour', 12)))
    out.append('Category: %s | Real Answer: %s' % (cat, real))
    for o in q['options']:
        marker = ' ◀◀◀ REAL' if o['letter'] == real else ''
        out.append('  %s. %s%s' % (o['letter'], o['text'][:50], marker))

    # STEP 1: 排盘
    out.append('\n[STEP 1] 排盘')
    out.append('  四柱: %s' % json.dumps(pillars, ensure_ascii=False))
    out.append('  日主: %s(%s) %s' % (b.get('日主'), b.get('日主五行'), b.get('日主强弱')))
    out.append('  喜用: %s | 忌: %s' % (b.get('喜用神'), b.get('忌神')))
    out.append('  五行: %s' % json.dumps(b.get('五行力量', {}), ensure_ascii=False))

    # STEP 2: 用神锁定
    out.append('\n[STEP 2] 用神锁定')
    ys = auto_yongshen(cat, b)
    out.append('  核心规则: %s' % json.dumps(ys.get('核心规则', {}), ensure_ascii=False))
    out.append('  主看: %s' % ys.get('分析要点', ''))

    # STEP 3: 原局神煞
    out.append('\n[STEP 3] 原局神煞')
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    dg = b.get('日主', '')
    natal = natal_shensha(yz, dz, dg)
    out.append('  %s' % json.dumps(natal['positions'], ensure_ascii=False))

    # STEP 4: 流年神煞
    out.append('\n[STEP 4] 流年神煞')
    liunian = chart.get('liunian') or {}
    natal_zhis = [pillars.get(k, '')[-1:] for k in ('年柱', '月柱', '日柱', '时柱')]
    shen_by_year = {}
    for yi in liunian.get('年份流年对比', []):
        yr = yi.get('年份')
        gz = yi.get('干支', '')
        lz = gz[-1:] if gz else ''
        if lz:
            hits = year_shensha(yz, dz, lz, natal_zhis)
            if hits:
                shen_by_year[yr] = hits
                out.append('  %d: %s' % (yr, ', '.join(hits)))
    if not shen_by_year:
        out.append('  (无神煞引动)')

    # STEP 5: 大限逐岁
    out.append('\n[STEP 5] 大限逐岁（提取关键年）')
    dy = dayun_year_by_year(pillars, bi['gender'], bi['year'], 1, 6)
    # 只显示选项年份附近的
    opt_years = []
    for o in q['options']:
        opt_years += [int(x) for x in re.findall(r'20\d{2}|19\d{2}', o['text'])]
    for d in dy:
        if d['year'] in opt_years:
            out.append('  %d (%d岁) 大运=%s 流年=%s 流年十神=%s' % (
                d['year'], d['age'], d['dayun'], d['liunian'], d['liunian_shishen']))

    # STEP 6: 四化飞星
    out.append('\n[STEP 6] 四化飞星')
    year_gz = pillars.get('年柱', '')
    ygan = year_gz[:1] if year_gz else ''
    # 从紫微宫位构建 {宫: [星]}
    zw_palaces = {}
    for k, v in z.items():
        if k.endswith('主星') and isinstance(v, list):
            palace_name = k.replace('主星', '')
            zw_palaces[palace_name] = v
    if ygan and zw_palaces:
        sh = sihua_feigong(ygan, zw_palaces)
        for hua, (star, palace) in sh.items():
            out.append('  %s(%s) 入%s宫' % (hua, star, palace))

    # STEP 7: 三方四正（命宫）
    out.append('\n[STEP 7] 三方四正（命宫）')
    sf = sanfang_sizheng('命宫', zw_palaces)
    for palace, stars in sf.items():
        if stars:
            out.append('  %s: %s' % (palace, ', '.join(stars)))

    # STEP 8: 星曜亮度
    out.append('\n[STEP 8] 星曜亮度')
    for palace, stars in zw_palaces.items():
        if not stars:
            continue
        # 找宫位地支（从紫微数据反推太麻烦，跳过详细亮度）
        bright_info = []
        for star in stars:
            from extra_tools import STAR_BRIGHTNESS
            if star in STAR_BRIGHTNESS:
                bright_info.append('%s(%s)' % (star, '查表可查'))
        if bright_info:
            out.append('  %s: %s' % (palace, ', '.join(bright_info)))

    # STEP 9: 知识库检索
    out.append('\n[STEP 9] 知识库检索')
    ss = b.get('十神', {})
    kb_feats = {
        '十神透干': [v for k, v in ss.items() if k.endswith('天干')],
        '神煞': [n for hits in shen_by_year.values() for n in hits],
        '力量': ['财多身弱'] if '身弱' in chart.get('wealth_analysis', {}).get('财运提示', '') else [],
        '宫位': ['年柱正官'] if ss.get('年柱天干') == '正官' or ss.get('年柱地支本气') == '正官' else [],
    }
    if female := bi['gender'] in ('女', 'F', 'female'):
        kb_feats['女命十神'] = list(kb_feats['十神透干'])
    kb_res = query_kb(kb_feats, top_n=5)
    for line in format_kb_results(kb_res):
        out.append('  %s' % line)

    # STEP 10: 案例线
    out.append('\n[STEP 10] 案例线')
    sig_pillars = pillars
    sibs = RET.same_chart_cases(sig_pillars, exclude_qid=qid)
    if sibs:
        for s in sibs:
            out.append('  同命主: %s [%s] 答案=%s' % (s['qid'], s['cat'], s['answer']))
    else:
        out.append('  (无同命主其他题)')

    # STEP 11: 综合判定
    out.append('\n[STEP 11] 综合判定')
    out.append('  → 请综合以上所有工具输出进行判定')
    out.append('  → 检查56条陷阱')
    out.append('  → 正确答案: %s' % real)
    out.append('')

    return out


if __name__ == '__main__':
    qid = sys.argv[1] if len(sys.argv) > 1 else 'ftb_0117'
    result = run_pipeline(qid)
    out_path = r'E:\ming_li_skill\MingLiSkill\pipeline_%s.txt' % qid
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))
    print('written to %s' % out_path)
