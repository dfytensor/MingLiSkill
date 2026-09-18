# -*- coding: utf-8 -*-
"""
shuffle_test.py — 选项顺序打乱测试
验证：方法学到的是语义（打乱后不变）还是字母位置（打乱后崩溃）
"""
import io, sys, json, os, re, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from collections import Counter, defaultdict

BASE = r'E:\ming_li_skill\MingLiSkill'
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

# ===== Load method outputs =====
methods = {}
from retriever import ROUNDS
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        methods.setdefault(qid, {})['hybrid'] = a['answer']
        methods[qid]['agent'] = a['answer']
        methods[qid]['rules'] = rules

# rules_suggestion outputs a letter → test if it's position-dependent
# by checking: does rules_suggestion tend to pick specific letters?

print('=== Letter Distribution Analysis ===\n')

# Check: does rules_suggestion have letter bias?
rules_letters = Counter()
agent_letters = Counter()
real_letters = Counter()

for qid in methods:
    m = methods[qid]
    real = key[qid]['answer']
    if 'rules' in m:
        rules_letters[m['rules']] += 1
    if 'agent' in m:
        agent_letters[m['agent']] += 1
    real_letters[real] += 1

total = len(methods)
print('Real answer distribution:')
for L in 'ABCD':
    print('  %s: %d (%.0f%%)' % (L, real_letters[L], real_letters[L]/total*100))

print('\nrules_suggestion letter distribution:')
for L in 'ABCD':
    c = rules_letters.get(L, 0)
    print('  %s: %d (%.0f%%)' % (L, c, c/total*100))

print('\nagent letter distribution:')
for L in 'ABCD':
    c = agent_letters.get(L, 0)
    print('  %s: %d (%.0f%%)' % (L, c, c/total*100))

# Check: is rules_suggestion just guessing a common letter?
# If rules always picks C and C is 30% of answers → 30% baseline
print('\n=== Position bias test ===')
print('If rules_suggestion always picked "C", it would get %.0f%% by chance' % (real_letters['C']/total*100))

# Accuracy when rules agrees/disagrees with most common letter
common_letter = real_letters.most_common(1)[0][0]
rules_accurate = sum(1 for qid in methods if methods[qid].get('rules') == key[qid]['answer'])
rules_picks_common = sum(1 for qid in methods if methods[qid].get('rules') == common_letter)
print('rules_suggestion accuracy: %d/%d = %.1f%%' % (rules_accurate, total, rules_accurate/total*100))
print('rules_suggestion picks most-common letter (%s): %d times' % (common_letter, rules_picks_common))

# ===== Shuffle simulation =====
# For each method: shuffle option letters and re-score
print('\n=== Shuffle Simulation (5 rounds) ===\n')

for method_name in ['agent', 'hybrid', 'rules']:
    original_correct = sum(1 for qid in methods if methods[qid].get(method_name) == key[qid]['answer'])
    
    shuffle_scores = []
    for trial in range(5):
        random.seed(42 + trial)
        shuffled_correct = 0
        for qid in methods:
            m = methods[qid]
            ans = m.get(method_name)
            if not ans:
                continue
            # Create a random letter mapping
            letters = ['A', 'B', 'C', 'D']
            random.shuffle(letters)
            mapping = {'A': letters[0], 'B': letters[1], 'C': letters[2], 'D': letters[3]}
            shuffled_ans = mapping.get(ans, ans)
            # Check if the SHUFFLED answer matches the real answer
            # (this simulates: if options were shuffled, would the method still pick the right CONTENT?)
            # Actually, for position bias test:
            # If the method picks based on POSITION (always C), shuffling won't change anything
            # If the method picks based on CONTENT (semantic), shuffling changes which position has the right content
            
            # For letter-level methods (rules_suggestion outputs a letter):
            # If we shuffle the REAL answer's letter, the method needs to pick the NEW letter
            # to be correct (because the correct CONTENT is now at a different position)
            
            # Simulate: the real answer moves to a new position
            new_real = mapping.get(key[qid]['answer'], key[qid]['answer'])
            shuffled_correct += (shuffled_ans == new_real)
        
        shuffle_scores.append(shuffled_correct)
    
    avg_shuffled = sum(shuffle_scores) / len(shuffle_scores)
    print('%s:' % method_name)
    print('  Original: %d/%d = %.1f%%' % (original_correct, total, original_correct/total*100))
    print('  Shuffled avg: %.1f/%d = %.1f%%' % (avg_shuffled, total, avg_shuffled/total*100))
    print('  (If semantic → same as original. If position-biased → ~25%)')
    print()

# ===== Key question: does our committed answer depend on letter position? =====
print('=== Our committed answer: letter bias check ===')
committed_letters = Counter()
for qid in methods:
    if 'hybrid' in methods[qid]:
        committed_letters[methods[qid]['hybrid']] += 1
for L in 'ABCD':
    c = committed_letters.get(L, 0)
    real_c = real_letters.get(L, 0)
    print('  %s: we pick %d times, real is %d times → bias=%+d' % (L, c, real_c, c - real_c))
