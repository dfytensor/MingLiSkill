# -*- coding: utf-8 -*-
"""
retriever.py — 轻量检索工具（零依赖）
- BM25Okapi（字符二元分词，适配中文）
- 正则/关键词加分层
- 两个索引:
  1) KB_INDEX   : 知识库断语（主题+断语+关键词）
  2) CASE_INDEX : 160题已答案例库（问题文本+排盘特征+最终答案）
- 同八字签名检索: chart_signature → 案例线（同一命主其他题的事实）
"""
import json
import re
from collections import Counter

ROUNDS = [
    ('blind15_charts.json', 'blind15_answers.json'),
    ('v5blind_charts.json', 'v5blind_answers.json'),
    ('blind30_charts.json', 'blind30_answers.json'),
    ('hybrid4_charts.json', 'hybrid4_answers.json'),
    ('hybrid5_charts.json', 'hybrid5_answers.json'),
    ('hybrid6_charts.json', 'hybrid6_answers.json'),
    ('hybrid7_charts.json', 'hybrid7_answers.json'),
    ('hybrid8_charts.json', 'hybrid8_answers.json'),
    ('hybrid9_charts.json', 'hybrid9_answers.json'),
]
BASE = r'E:\ming_li_skill\MingLiSkill'


def tokenize(text):
    """中文按字+二元组，ASCII 按词。"""
    text = re.sub(r'\s+', '', str(text))
    toks = []
    buf = ''
    for ch in text:
        if re.match(r'[a-zA-Z0-9]', ch):
            buf += ch
        else:
            if buf:
                toks.append(buf.lower())
                buf = ''
            if re.match(r'[\u4e00-\u9fff]', ch):
                toks.append(ch)
    if buf:
        toks.append(buf.lower())
    # bigrams
    bi = [text[i:i + 2] for i in range(len(text) - 1)]
    return toks + bi


class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = []
        self.doc_lens = []
        self.tf = []
        self.df = Counter()
        self.avgdl = 0.0

    def add(self, doc_tokens):
        self.docs.append(doc_tokens)
        self.doc_lens.append(len(doc_tokens))
        cnt = Counter(doc_tokens)
        self.tf.append(cnt)
        for t in cnt:
            self.df[t] += 1

    def finalize(self):
        self.N = len(self.docs)
        self.avgdl = sum(self.doc_lens) / max(self.N, 1)

    def search(self, query_tokens, top_k=5):
        scores = []
        for i in range(self.N):
            s = 0.0
            dl = self.doc_lens[i]
            for t in set(query_tokens):
                f = self.tf[i].get(t, 0)
                if not f:
                    continue
                n = self.df[t]
                idf = __import__('math').log((self.N - n + 0.5) / (n + 0.5) + 1)
                s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            scores.append((s, i))
        scores.sort(key=lambda x: -x[0])
        return [(s, i) for s, i in scores[:top_k] if s > 0]


def chart_signature(pillars):
    p = pillars or {}
    return ''.join(p.get(k, '?') for k in ('年柱', '月柱', '日柱', '时柱'))


def load_cases():
    """载入160题案例: {qid, cat, question, options_text, signature, answer, reason}"""
    import os
    cases = []
    for cf, af in ROUNDS:
        p1 = os.path.join(BASE, cf)
        p2 = os.path.join(BASE, af)
        if not (os.path.exists(p1) and os.path.exists(p2)):
            continue
        charts = {c['id']: c for c in json.load(open(p1, encoding='utf-8'))}
        answers = json.load(open(p2, encoding='utf-8'))
        keyfile = r'F:\牛逼模型\MingLi-Bench\data\data.json'
        data = json.load(open(keyfile, encoding='utf-8'))
        key = {q['id']: q for q in data['questions']}
        for qid, a in answers.items():
            c = charts[qid]
            q = key[qid]
            pillars = c['chart_data'].get('bazi', {}).get('四柱', {})
            cases.append({
                'qid': qid,
                'cat': q.get('category', ''),
                'question': q.get('question', ''),
                'options_text': ' '.join(o['text'] for o in q.get('options', [])),
                'signature': chart_signature(pillars),
                'pillars': pillars,
                'answer': a['answer'],
                'reason': a.get('reason', ''),
            })
    return cases


class Retriever:
    """统一检索入口: KB断语 + 案例库(BM25+同八字签名)"""

    def __init__(self):
        from knowledge_base import KB
        self.kb = KB
        self.kb_bm = BM25()
        for e in self.kb:
            self.kb_bm.add(tokenize(e['主题'] + e['断语'] + ''.join(e['关键词'])))
        self.kb_bm.finalize()

        self.cases = load_cases()
        self.case_bm = BM25()
        for c in self.cases:
            self.case_bm.add(tokenize(c['question'] + c['options_text'] + c['cat']))
        self.case_bm.finalize()
        # 同八字签名索引
        self.sig_index = {}
        for c in self.cases:
            self.sig_index.setdefault(c['signature'], []).append(c)

    def search_kb(self, text, top_k=5):
        toks = tokenize(text)
        out = []
        for s, i in self.kb_bm.search(toks, top_k):
            e = self.kb[i]
            # 关键词正则加分
            kw_hit = sum(1 for kw in e['关键词'] if re.search(kw, text))
            out.append({'score': s + kw_hit * 2.0, '主题': e['主题'],
                        '断语': e['断语'], '关键词': e['关键词']})
        out.sort(key=lambda x: -x['score'])
        return out

    def search_cases(self, text, top_k=5, exclude_qid=None, same_cat_boost=True):
        toks = tokenize(text)
        out = []
        for s, i in self.case_bm.search(toks, top_k + 5):
            c = self.cases[i]
            if c['qid'] == exclude_qid:
                continue
            out.append({'score': s, 'case': c})
        out.sort(key=lambda x: -x['score'])
        return out[:top_k]

    def same_chart_cases(self, pillars, exclude_qid=None):
        sig = chart_signature(pillars)
        return [c for c in self.sig_index.get(sig, []) if c['qid'] != exclude_qid]


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    r = Retriever()
    print('cases loaded: %d | same-chart groups: %d' % (len(r.cases), len(r.sig_index)))
    demo = r.search_kb('女命流年伤官透干 结婚还是分手 官非')
    for d in demo[:3]:
        print('KB:', d['主题'], '|', d['断语'][:30])
    demo2 = r.search_cases('什么时候结婚 配偶宫合动')
    for d in demo2[:3]:
        print('CASE:', d['case']['qid'], d['case']['cat'], '->', d['case']['answer'])
