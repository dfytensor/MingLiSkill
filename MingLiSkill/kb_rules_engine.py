# -*- coding: utf-8 -*-
"""
kb_rules_engine.py — 知识库增强确定性规则引擎
对 160 题逐题: 特征提取 → KB(含扩展包)检索 → 选项关键词打分 → 取最高分。
确定性、一次运行、无逐题调参。对比基线: 规则引擎 33.75%。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.shensha import natal_shensha
from tools.calendar_engine import changsheng_state
from knowledge_base import query_kb, KB
from knowledge_ext import KB_EXT

ALL_KB = KB + KB_EXT
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
HTK = HybridMingliToolkit()

SEASON = {'寅': '春', '卯': '春', '辰': '春', '巳': '夏', '午': '夏', '未': '夏',
          '申': '秋', '酉': '秋', '戌': '秋', '亥': '冬', '子': '冬', '丑': '冬'}


def kb_query_ext(features, top_n=10):
    """扩展检索: 支持 调候(日主×月支 conjunction)。"""
    results = []
    for e in ALL_KB:
        trig = e['触发']
        hits = 0
        need_all = False
        if '调候' in trig:
            need_all = True
        for k, vals in trig.items():
            fv = features.get(k, [])
            if isinstance(fv, str):
                fv = [fv]
            if need_all and k == '调候':
                continue
            for v in vals:
                if v in fv:
                    hits += 1
                    break
        # 调候: 日主 in 且 出生月支 in
        if '调候' in trig:
            if rec_check(features, trig['调候']):
                hits += 1
            else:
                continue
        if hits > 0:
            results.append((hits, e))
    results.sort(key=lambda x: -x[0])
    return results[:top_n]


def rec_check(features, kw_list):
    for kw in kw_list:
        try:
            d, s = kw.split('-')
            if features.get('日主') == d and s in features.get('季节', []):
                return True
        except ValueError:
            pass
    return False


def build_features(q, chart, liunian):
    b = chart['bazi']
    gender = q['birth_info']['gender']
    female = gender in ('女', 'F', 'female')
    ss = b.get('十神', {})
    tg = {k: v for k, v in ss.items() if k.endswith('天干')}
    f = {
        '日主': b.get('日主', ''),
        '十神透干': sorted(set(tg.values())),
        '十神': sorted(set(ss.values())),
        '神煞': [],
        '结构': [],
        '宫位': [],
        '流年': [],
        '力量': [],
        '五行': [],
        '长生位': [],
        '干支': [],
        '季节': [],
    }
    if female:
        f['女命十神'] = list(f['十神透干'])
        if '伤官' in tg.values():
            f['女命十神'].append('伤官透干')
        vals = list(ss.values())
        if '正官' in vals and '七杀' in vals:
            f['女命十神'].append('官杀混杂')
    else:
        f['男命十神'] = list(f['十神透干'])
        if '正财' in tg.values() and '偏财' in tg.values():
            f['男命十神'].append('正偏财混杂')
    wa = chart.get('wealth_analysis', {}).get('财运提示', '')
    if '身弱' in wa:
        f['力量'].append('财多身弱')
    if '身旺' in wa:
        f['力量'].append('身旺任财')
    ha = chart.get('health_analysis', {})
    if ha.get('最弱五行'):
        f['五行'].append('最弱五行')
    # 调候特征
    pillars = b.get('四柱', {})
    mgz = pillars.get('月柱', '')
    if mgz:
        f['季节'].append(SEASON.get(mgz[-1], ''))
    # 神煞(原局+流年)
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    natal = natal_shensha(yz, dz, b.get('日主', ''))
    for p, n in natal['positions'].items():
        f['神煞'].append(n)
    natal_zhis = [pillars.get(k, '')[-1:] for k in ('年柱', '月柱', '日柱', '时柱')]
    for yi in (liunian or {}).get('年份流年对比', []):
        gz = yi.get('干支', '')
        lz_zhi = gz[-1:] if gz else ''
        if lz_zhi:
            try:
                for h in year_shen_safe(yz, dz, lz_zhi, natal_zhis):
                    name = h.split('(')[0]
                    f['神煞'].append(name)
                    if '三刑' in h:
                        f['结构'].append('三刑')
            except Exception:
                pass
        # 流年长生位(日主于流年支)
        try:
            st = changsheng_state(b.get('日主', ''), lz_zhi)
            if st:
                f['长生位'].append(st)
        except Exception:
            pass
        gan_ss = yi.get('天干十神', '')
        if gan_ss:
            f['流年'].append(gan_ss + '透干')
            if female and gan_ss in ('食神', '伤官'):
                f['流年'].append('食伤透干(女)')
            if female and gan_ss == '七杀':
                f['流年'].append('七杀透干(女)')
    # 干支类象: 原局+流年天干地支
    f['干支'] += [pillars.get(k, '')[:1] for k in ('年柱', '月柱', '日柱', '时柱') if pillars.get(k)]
    f['干支'] += natal_zhis
    for yi in (liunian or {}).get('年份流年对比', []):
        gz = yi.get('干支', '')
        f['干支'] += [gz[:1], gz[-1:]]
    # 宫位
    if ss.get('年柱天干') == '伤官' or ss.get('年柱地支本气') == '伤官':
        f['宫位'].append('年柱伤官')
    if ss.get('月柱天干') == '伤官' or ss.get('月柱地支本气') == '伤官':
        f['宫位'].append('月柱伤官')
    if ss.get('时柱天干') == '正印' or ss.get('时柱地支本气') == '正印':
        f['宫位'].append('时柱正印')
    if ss.get('日柱地支本气') == '偏印':
        f['宫位'].append('日坐偏印')
    if ss.get('年柱天干') == '正官' or ss.get('年柱地支本气') == '正官':
        f['宫位'].append('年柱正官')
    if ss.get('年柱天干') in ('正财', '偏财') or ss.get('年柱地支本气') in ('正财', '偏财'):
        f['宫位'].append('年柱财星')
    kong = b.get('空亡', [])
    day_zhi = pillars.get('日柱', '')[-1:]
    if day_zhi in kong:
        f['宫位'].append('配偶宫空亡')
    if ss.get('日柱地支本气') == '伤官' and female:
        f['宫位'].append('配偶宫坐伤官(女)')
    # 结构: 财多坏印/身弱
    wx = b.get('五行力量', {})
    day_wx = b.get('日主五行', '')
    yin_wx = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}.get(day_wx)
    cai_wx = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}.get(day_wx)
    if yin_wx and cai_wx and wx.get(cai_wx, 0) > 2.5 and wx.get(yin_wx, 9) < 1.5:
        f['结构'].append('财多坏印')
    # 官星/夫星入墓: 官杀五行墓位与原局/流年支
    guan_wx = {'木': '火', '火': '金', '土': '木', '金': '火', '水': '土'}.get(day_wx)  # approx: not used strictly
    # 妻星受劫/母星受克: 粗判——流年天干十神
    return f


def year_shen_safe(yz, dz, lz_zhi, natal_zhis):
    from tools.shensha import year_shensha
    return year_shensha(yz, dz, lz_zhi, natal_zhis)


def kw_in(text, kws):
    c = 0
    for kw in kws:
        try:
            if re.search(kw, text):
                c += 1
        except re.error:
            if kw in text:
                c += 1
    return c


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    correct = total = 0
    cat_stats = {}
    detail = []
    for q in data['questions']:
        qid = q['id']
        bi = q['birth_info']
        try:
            r = HTK.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=q['category'], question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            chart = json.loads(r)
        except Exception:
            continue
        liunian = chart.get('liunian') or {}
        feats = build_features(q, chart, liunian)
        res = kb_query_ext(feats, top_n=12)
        opt_texts = {o['letter']: o['text'] for o in q['options']}
        scores = {L: 0.0 for L in opt_texts}
        for hits, e in res:
            w = 1.0 * hits
            if e['主题'] == q['category']:
                w *= 1.5
            for L, txt in opt_texts.items():
                scores[L] += w * kw_in(txt, e['关键词'])
        best = max(scores, key=lambda L: scores[L])
        if scores[best] == 0:
            best = chart.get('rules_suggestion', {}).get('suggested_answer', best)
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(q['category'], [0, 0])
        cat_stats[q['category']][0] += ok
        cat_stats[q['category']][1] += 1
        detail.append('%s %-4s kb=%s -> %s (real %s) %s' % (
            qid, q['category'], best, '', real, 'OK' if ok else 'X'))
    lines = ['KB rules engine: %d/%d = %.1f%%  (baseline rules 33.75%% / agent 40%%)' % (
        correct, total, correct / total * 100 if total else 0)]
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d' % (cat, s[0], s[1]))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\kb_engine_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('KB ENGINE: %d/%d = %.1f%%' % (correct, total, correct / total * 100 if total else 0))


if __name__ == '__main__':
    main()
