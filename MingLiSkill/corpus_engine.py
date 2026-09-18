# -*- coding: utf-8 -*-
"""
corpus_engine.py — 语料检索引擎
1.6MB 经典语料(渊海子平/滴天髓阐微/八字手册) → 断语切分 → BM25 → 主题断言抽取 → 选项匹配。
确定性一次运行全量 160 题。
"""
import io, sys, os, json, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from retriever import BM25, tokenize
from tools import HybridMingliToolkit

HTK = HybridMingliToolkit()

CORPUS = r'E:\ming_li_skill\MingLiSkill\corpus'
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'

# 经典断语主题词表（固定，非针对benchmark调参）
THEME_LEX = {
    '婚': ['结婚', '娶', '嫁', '婚', '妻', '夫', '配偶', '成家', '洞房'],
    '离': ['离婚', '离', '克妻', '克夫', '刑妻', '丧妻', '丧夫', '再婚', '二婚', '婚变'],
    '恋': ['恋爱', '桃花', '情', '妾', '外遇', '风流', '色'],
    '子': ['子', '子女', '儿', '女', '生育', '产', '孕', '嗣'],
    '财': ['财', '富', '发财', '得财', '置业', '产业', '买卖'],
    '贫': ['贫', '穷', '破财', '失利', '亏', '债', '寒'],
    '病': ['病', '疾', '伤', '残疾', '夭', '亡', '死', '丧', '寿'],
    '官': ['官', '贵', '功名', '仕途', '公职', '权'],
    '讼': ['讼', '牢', '狱', '刑', '官非', '罪'],
    '迁': ['迁', '移', '出行', '远行', '出国', '驿马', '旅行'],
    '学': ['学', '文', '读书', '功名', '科举', '文昌', '才华'],
    '孤': ['孤', '寡', '独', '僧', '道', '尼', '出家'],
    '性': ['性', '心', '刚', '柔', '急', '躁', '仁', '智', '贪', '吝'],
    '六亲': ['父母', '母', '父', '兄弟', '姊妹', '祖'],
}
LEX_WORD = sorted({w for ws in THEME_LEX.values() for w in ws}, key=len, reverse=True)


def load_units():
    units = []
    for fn in os.listdir(CORPUS):
        p = os.path.join(CORPUS, fn)
        try:
            raw = open(p, 'rb').read()
            try:
                txt = raw.decode('utf-8')
            except UnicodeDecodeError:
                txt = raw.decode('gbk', errors='replace')
        except Exception:
            continue
        # 去markdown符号
        txt = re.sub(r'[#*`>\-\|]+', ' ', txt)
        for piece in re.split(r'[。！？!?\n;；]+', txt):
            piece = piece.strip()
            hanzi = len(re.findall(r'[\u4e00-\u9fff]', piece))
            if 12 <= len(piece) <= 220 and hanzi >= 10:
                units.append({'file': fn, 'text': piece})
    return units


def unit_themes(unit_text):
    hits = []
    for theme, words in THEME_LEX.items():
        for w in words:
            if w in unit_text:
                hits.append(theme)
                break
    return hits


def build_feature_query(q, chart, liunian):
    b = chart['bazi']
    ss = b.get('十神', {})
    tg = [v for k, v in ss.items() if k.endswith('天干')]
    terms = []
    terms += sorted(set(tg))
    wa = chart.get('wealth_analysis', {}).get('财运提示', '')
    if '身弱' in wa:
        terms.append('财多身弱')
    if '身旺' in wa:
        terms.append('身旺任财')
    hu = chart.get('huoyuan_analysis', {})
    if hu.get('格局'):
        terms.append(hu['格局'])
    ca = chart.get('career_analysis', {}).get('格局倾向', '')
    if ca:
        terms.append(ca)
    # 结构词
    wx = b.get('五行力量', {})
    day_wx = b.get('日主五行', '')
    yin_wx = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}.get(day_wx)
    cai_wx = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}.get(day_wx)
    if yin_wx and cai_wx and wx.get(cai_wx, 0) > 2.5 and wx.get(yin_wx, 9) < 1.5:
        terms.append('财多坏印')
    # 女命
    if q['birth_info']['gender'] in ('女', 'F', 'female'):
        if '伤官' in tg:
            terms.append('女命伤官')
        vals = list(ss.values())
        if '正官' in vals and '七杀' in vals:
            terms.append('官杀混杂')
    else:
        if '正财' in tg and '偏财' in tg:
            terms.append('正偏财混杂')
    # 神煞
    for yi in (liunian or {}).get('年份流年对比', []):
        for t in yi.get('标签', []):
            if '神煞:' in t:
                terms.append(t.split('神煞:')[1].split('(')[0])
    # 日主+月支调候
    pillars = b.get('四柱', {})
    terms.append('日主' + b.get('日主', ''))
    mgz = pillars.get('月柱', '')
    if mgz:
        terms.append('月' + mgz[-1])
    return ' '.join(terms)


def main():
    print('loading corpus...')
    units = load_units()
    print('units: %d' % len(units))
    bm = BM25()
    for u in units:
        bm.add(tokenize(u['text']))
    bm.finalize()

    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)

    correct = total = 0
    cat_stats = {}
    detail = []
    for q in data['questions']:
        bi = q['birth_info']
        try:
            r = HTK.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=q['category'], question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            chart = json.loads(r)
        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.stderr.write('FAILED at %s\n' % q['id'])
            if total == 0 and correct == 0:
                break
            continue
        liunian = chart.get('liunian') or {}
        query = build_feature_query(q, chart, liunian)
        hits = bm.search(tokenize(query), top_k=40)
        # 主题打分
        theme_score = Counter()
        for s, i in hits:
            for th in unit_themes(units[i]['text']):
                theme_score[th] += s
        # 选项打分: 选项文本命中的主题词→主题分
        opt_texts = {o['letter']: o['text'] for o in q['options']}
        scores = {}
        for L, txt in opt_texts.items():
            sc = 0.0
            for theme, words in THEME_LEX.items():
                for w in words:
                    if w in txt:
                        sc += theme_score.get(theme, 0)
            scores[L] = sc
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
        detail.append('%s %-4s -> %s (real %s) %s | themes=%s' % (
            q['id'], q['category'], best, real, 'OK' if ok else 'X',
            dict(theme_score.most_common(4))))

    lines = ['CORPUS ENGINE: %d/%d = %.1f%% (baselines: rules 33.75%%, hybrid 40.0%%)' % (
        correct, total, correct / total * 100 if total else 0)]
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d' % (cat, s[0], s[1]))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\corpus_engine_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('CORPUS ENGINE: %d/%d = %.1f%%' % (correct, total, correct / total * 100 if total else 0))


if __name__ == '__main__':
    main()
