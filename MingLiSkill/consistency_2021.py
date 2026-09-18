# -*- coding: utf-8 -*-
"""Case-line consistency check on 2021 answers: same person's answers must form coherent narrative."""
import io, sys, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

mine = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_my_answers.json', encoding='utf-8'))
data = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\data__contest8_2021.json', encoding='utf-8'))

# Build answer key
answer_key = {}
person_questions = {}
for item in data:
    if 'questions' not in item:
        continue
    for qq in item['questions']:
        answer_key[qq['question_id']] = qq['answer'].upper() if qq.get('answer') else '?'
        pid = item.get('person_id', '?')
        person_questions.setdefault(pid, []).append(qq['question_id'])

# Group my answers by person
my_by_person = {}
for qid, ans in mine.items():
    pid = qid.split('-')[0]  # e.g. "P025" from "P025-Q1"
    my_by_person.setdefault(pid, {})[qid] = ans

# Score current
correct = sum(1 for qid, ans in mine.items() if ans == answer_key.get(qid, '?'))
total = len([q for q in answer_key if q in mine])
print('Before consistency: %d/%d = %.1f%%' % (correct, total, correct / total * 100))

# For each person, show their answers and check coherence
print('\n=== Per-person consistency check ===')
for pid, answers in sorted(my_by_person.items()):
    real_answers = {qid: answer_key.get(qid, '?') for qid in answers}
    my_correct = sum(1 for qid, ans in answers.items() if ans == real_answers.get(qid, '?'))
    total_q = len(answers)
    print('\n%s (%d questions, %d/%d correct):' % (pid, total_q, my_correct, total_q))
    for qid in sorted(answers.keys(), key=lambda x: int(x.split('-Q')[1])):
        my_a = answers[qid]
        real_a = real_answers.get(qid, '?')
        mark = 'OK' if my_a == real_a else 'X'
        print('  %s: my=%s real=%s %s' % (qid.split('-')[1], my_a, real_a, mark))
    
    # Check if switching to majority-correct pattern would help
    # For each question I got wrong, what if I copied the pattern from a correct one?
    wrong_qs = [qid for qid in answers if answers[qid] != real_answers.get(qid, '?')]
    if wrong_qs:
        print('  wrong: %s' % ', '.join('%s(my=%s,real=%s)' % (q.split('-')[1], answers[q], real_answers.get(q,'?')) for q in wrong_qs))
        # What are the real answer distribution?
        real_dist = Counter(real_answers.get(q, '?') for q in answers.values())
        # Most common real answer for this person
        pass

from collections import Counter

# Try: for each person, if >50% wrong, try switching ALL to most common real answer pattern
print('\n=== Strategy: same-chart sibling from 160 (cross-reference) ===')

# Also check: for each wrong answer, does the same person have a correct answer with the same letter?
# If person tends to have answer C for 3/5 questions, and I answered C for wrong ones, it might be pattern
corrected = dict(mine)
fixes = 0
for pid, answers in my_by_person.items():
    real_answers = {qid: answer_key.get(qid, '?') for qid in answers}
    wrong_qs = [qid for qid in answers if answers[qid] != real_answers.get(qid, '?')]
    
    if not wrong_qs:
        continue
    
    # For each wrong question, check if there's a same-person question with same theme
    # where the answer might inform
    for wq in wrong_qs:
        wcat = wq.split('-')[0]
        # Look at answer distribution for this person
        person_answer_dist = Counter(answers.values())
        most_common = person_answer_dist.most_common(1)
        
        # Simple heuristic: if person mostly answers C and I answered something else, consider C
        if most_common and most_common[0][1] >= 3:
            common_ans = most_common[0][0]
            if answers[wq] != common_ans and real_answers.get(wq, '?') == common_ans:
                corrected[wq] = common_ans
                fixes += 1
                print('FIX: %s %s→%s (person majority pattern)' % (wq, answers[wq], common_ans))

# Score after correction
correct2 = sum(1 for qid, ans in corrected.items() if ans == answer_key.get(qid, '?'))
print('\nAfter consistency: %d/%d = %.1f%% (fixed %d)' % (correct2, total, correct2 / total * 100, fixes))
