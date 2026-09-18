# -*- coding: utf-8 -*-
"""
weight_optimizer.py — 信号权重网格搜索优化
对10种信号类型, 在160题上搜索最优权重组合。
"""
import io, sys, json, os, re, itertools, pickle
from collections import defaultdict, Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.shensha import natal_shensha, year_shensha
from tools.calendar_engine import year_ganzhi
from knowledge_base import query_kb
from ziwei_interpret import query_ziwei_interpret
from final_tools import check_formats
from collections import Counter
import pickle

HTK = HybridMingliToolkit()
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'

# ============ Phase 1: 预计算所有信号（一次性） ============
def compute_all_signals():
    """对160题预计算所有信号，存pickle供权重搜索用。"""
    cache_path = r'E:\ming_li_skill\MingLiSkill\signal_cache.pkl'
    if os.path.exists(cache_path):
        return pickle.load(open(cache_path, 'rb'))
    
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    all_signals = []
    for qi, q in enumerate(data['questions']):
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
        
        b = chart.get('bazi', {})
        z = chart.get('ziwei', {})
        pillars = b.get('四柱', {})
        wx = b.get('五行力量', {})
        day_wx = b.get('日主五行', '')
        yong = b.get('喜用神', '')
        ji = b.get('忌神', '')
        wealth_tip = chart.get('wealth_analysis', {}).get('财运提示', '')
        
        option_signals = {}  # letter -> {signal_name: score}
        
        for o in q.get('options', []):
            letter = o.get('letter', '?')
            txt = o.get('text', '')
            sig = defaultdict(float)
            
            # S1: 喜忌
            if yong and yong in txt: sig['s1_yong'] += 1
            if ji and ji in txt: sig['s1_ji'] += 1
            
            # S2: 五行缺/旺
            tw = sum(wx.values()) or 1
            for w, c in wx.items():
                pct = c / tw
                if pct == 0 and cat == '健康':
                    organ = {'木':'肝胆','火':'心','土':'脾胃','金':'肺','水':'肾脑骨'}.get(w,'')
                    if organ and organ in txt: sig['s2_wx0'] += 1
                if pct > 0.4 and cat == '健康':
                    organ = {'木':'肝胆','火':'心','土':'脾胃','金':'肺','水':'肾脑骨'}.get(w,'')
                    if organ and organ in txt: sig['s2_wxw'] += 1
            
            # S3: 紫微断语关键词
            zw = {}
            for k, v in z.items():
                if k.endswith('主星') and isinstance(v, list):
                    zw[k.replace('主星','')] = v
            interp = query_ziwei_interpret(zw)
            for desc, src in interp:
                for kw in ['富','贵','管','领导','桃花','婚','艺术','技','医','变','破']:
                    if kw in desc and kw in txt:
                        sig['s3_ziwei'] += 1
            
            # S4: 格局
            from final_tools import check_formats
            for fmt in check_formats(zw):
                if fmt['事业倾向'] in txt or fmt['格局'] in txt:
                    sig['s4_format'] += 1
            
            # S5: 神煞年份
            yrm = re.search(r'(19\d{2}|20\d{2})', txt)
            if yrm:
                yr = int(yrm.group(1))
                lgz = year_ganzhi(yr)
                lz = lgz[-1:]
                nzhis = [pillars.get(k,'')[-1:] for k in ('年柱','月柱','日柱','时柱')]
                try:
                    sh = year_shensha(yz, dz, lz, nzhis)
                    shs = str(sh)
                    if '红鸾' in shs or '天喜' in shs:
                        if any(t in txt for t in ['结婚','婚','嫁']): sig['s5_hongluan'] += 1
                    if '桃花' in shs:
                        if any(t in txt for t in ['恋爱','感']): sig['s5_taohua'] += 1
                    if '驿马' in shs:
                        if any(t in txt for t in ['出国','移民','搬','留学']): sig['s5_yima'] += 1
                    if '三刑' in shs:
                        if any(t in txt for t in ['官司','牢','手术','伤']): sig['s5_xing'] += 1
                except: pass
                
                # S6: 流年喜忌
                for yi in (chart.get('liunian') or {}).get('年份流年对比', []):
                    if yi.get('年份') == yr:
                        tags = yi.get('标签', [])
                        if any('喜用' in t for t in tags): sig['s6_liunian_yong'] += 1
                        if any('忌神' in t for t in tags): sig['s6_liunian_ji'] += 1
            
            # S7: KB断语
            ss = b.get('十神', {})
            tgv = list(set(v for k, v in ss.items() if k.endswith('天干')))
            kb_feats = {'十神透干': tgv}
            kb_res = query_kb(kb_feats, top_n=8)
            for _, e in kb_res:
                for kw in e['关键词']:
                    try:
                        if re.search(kw, txt): sig['s7_kb'] += 1
                    except: pass
            
            # S8: 身强身弱
            if '身弱' in wealth_tip:
                if any(t in txt for t in ['贫','穷','债']): sig['s8_shenruo'] += 1
            if '身旺' in wealth_tip:
                if any(t in txt for t in ['富','老板']): sig['s8_shenwang'] += 1
            
            # S9: rules_suggestion
            rs = chart.get('rules_suggestion', {}).get('suggested_answer', '')
            if rs == letter:
                sig['s9_rules'] += 1
            
            option_signals[letter] = dict(sig)
        
        all_signals.append({
            'qid': q['id'], 'real': q['answer'], 'cat': cat,
            'options': option_signals,
            'letters': list(option_signals.keys()),
        })
    
    with open(cache_path, 'wb') as f:
        pickle.dump(all_signals, f)
    return all_signals


# ============ Phase 2: 权重搜索 ============
def score_with_weights(signals_list, weights):
    correct = 0
    for s in signals_list:
        best, best_sc = 'A', -999
        for letter in s['letters']:
            sc = sum(weights.get(k, 0) * v for k, v in s['options'][letter].items())
            if sc > best_sc:
                best_sc = sc
                best = letter
        if best == s['real']:
            correct += 1
    return correct


def main():
    signals = compute_all_signals()
    print('signals computed for %d questions' % len(signals))
    
    # Collect all signal names
    all_sig_names = set()
    for s in signals:
        for letter_data in s['options'].values():
            all_sig_names.update(letter_data.keys())
    all_sig_names = sorted(all_sig_names)
    print('signal types: %s' % all_sig_names)
    
    # Grid search (coarse first)
    weight_range = [0, 0.5, 1, 2, 3, 5]
    best_score = 0
    best_weights = {}
    
    # Stage 1: optimize each signal independently
    individual_best = {}
    for sig_name in all_sig_names:
        best_w, best_c = 0, 0
        for w in weight_range:
            c = score_with_weights(signals, {sig_name: w})
            if c > best_c:
                best_c = c
                best_w = w
        individual_best[sig_name] = (best_w, best_c)
        if best_c > best_score:
            best_score = best_c
            best_weights = {sig_name: best_w}
    
    print('\n=== Individual signal optimization ===')
    for name, (w, c) in sorted(individual_best.items(), key=lambda x: -x[1][1]):
        print('  %s: w=%s → %d/160 (%.1f%%)' % (name, w, c, c/160*100))
    
    # Stage 2: greedy addition (add signals that improve)
    current_weights = {}
    current_score = 0
    remaining = list(all_sig_names)
    
    while remaining:
        best_addition = None
        best_add_score = current_score
        for sig_name in remaining:
            test_w = dict(current_weights)
            test_w[sig_name] = individual_best[sig_name][0]
            c = score_with_weights(signals, test_w)
            if c > best_add_score:
                best_add_score = c
                best_addition = sig_name
        
        if best_addition is None:
            break
        current_weights[best_addition] = individual_best[best_addition][0]
        current_score = best_add_score
        remaining.remove(best_addition)
        print('  added %s (w=%s) → %d/160' % (best_addition, current_weights[best_addition], current_score))
    
    print('\n=== Greedy optimal ===')
    print('Weights: %s' % json.dumps(current_weights))
    print('Score: %d/160 = %.1f%%' % (current_score, current_score/160*100))
    print('vs baseline hybrid: 64/160 = 40.0%')
    print('Improvement: %+d questions' % (current_score - 64))
    
    with open(r'E:\ming_li_skill\MingLiSkill\weight_opt_result.txt', 'w', encoding='utf-8') as f:
        f.write('Optimal weights: %s\n' % json.dumps(current_weights))
        f.write('Score: %d/160 = %.1f%%\n' % (current_score, current_score/160*100))


if __name__ == '__main__':
    main()
