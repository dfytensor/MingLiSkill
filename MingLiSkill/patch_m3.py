# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'E:\ming_li_skill\MingLiSkill\marriage_fix_v3.py'
c = open(p, encoding='utf-8').read()

# 1. add ZiweiToolkit import
old = "from tools import HybridMingliToolkit\nfrom tools.calendar_engine import shi_shen"
new = "from tools import HybridMingliToolkit\nfrom tools.calendar_engine import shi_shen\nfrom tools.ziwei_tools import ZiweiToolkit\nZT = ZiweiToolkit()"
assert old in c; c = c.replace(old, new)

# 2. negation filter on year options for wedding questions
old2 = """    years = {}
    mq = re.search(r'(19|20)\\d\\d', q['question'])
    if mq: years[int(mq.group(0))] = None
    for o in opts:
        for m in re.finditer(r'(19|20)\\d\\d', o['text']):
            years.setdefault(int(m.group(0)), o['letter'])"""
new2 = """    years = {}
    neg_kw = ['单身','未婚','沒有','没有','未嫁','未娶']
    mq = re.search(r'(19|20)\\d\\d', q['question'])
    if mq: years[int(mq.group(0))] = None
    is_wed_pre = any(k in alltxt for k in ['结婚','結婚','成婚','娶','嫁'])
    for o in opts:
        if is_wed_pre and any(k in o['text'] for k in neg_kw):
            continue  # 非结婚选项(如"到2022为止单身")不参与年份候选
        for m in re.finditer(r'(19|20)\\d\\d', o['text']):
            years.setdefault(int(m.group(0)), o['letter'])"""
assert old2 in c; c = c.replace(old2, new2)

# 3. S6 武破晚婚 before year scoring (restore from v13)
old3 = """    # 年份题
    if years and (is_wed or is_div or is_date):"""
new3 = """    # S6: 夫妻宫武曲/破军 → 晚婚 → 选最晚纯年份选项 (恢复v13规则)
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
                    if re.fullmatch(r'\\s*(19|20)\\d\\d\\s*年?\\s*', o['text']):
                        m = re.search(r'(19|20)\\d\\d', o['text'])
                        pure.append((o['letter'], int(m.group(0))))
                if pure:
                    latest = max(pure, key=lambda t: t[1])
                    return latest[0], 'S6:夫妻宫武破→最晚%d' % latest[1]
        except:
            pass

    # 年份题
    if years and (is_wed or is_div or is_date):"""
assert old3 in c; c = c.replace(old3, new3)

open(p, 'w', encoding='utf-8').write(c)
print('patched S6+filter')
