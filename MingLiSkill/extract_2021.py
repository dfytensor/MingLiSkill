# -*- coding: utf-8 -*-
"""Extract 2021 questions, check overlap with existing 160, prepare for pipeline test."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\data__contest8_2021.json', encoding='utf-8'))

# Extract all questions
questions = []
for item in d:
    if 'questions' not in item:
        continue
    profile = item.get('profile', {})
    birth = profile.get('birth', {})
    gender = profile.get('gender', '')
    person_id = item.get('person_id', '')
    
    for qq in item.get('questions', []):
        questions.append({
            'question_id': qq.get('question_id', ''),
            'person_id': person_id,
            'birth': birth,
            'gender': gender,
            'question': qq.get('question', ''),
            'options': qq.get('options', []),
            'answer': qq.get('answer', ''),
        })

print('total questions extracted: %d' % len(questions))
print('unique persons: %d' % len(set(q['person_id'] for q in questions)))

# Check overlap with existing 160 by birth date
existing = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
existing_births = set()
for q in existing['questions']:
    bi = q['birth_info']
    existing_births.add((bi['year'], bi['month'], bi['day']))

overlap = 0
new_questions = []
for qq in questions:
    b = qq['birth']
    birth_key = (b['year'], b['month'], b['day'])
    if birth_key in existing_births:
        overlap += 1
    else:
        new_questions.append(qq)

print('overlap with existing 160: %d questions' % overlap)
print('truly new questions: %d' % len(new_questions))

# Show all questions
for i, qq in enumerate(questions):
    b = qq['birth']
    out = 'Q%d [%s] %d-%02d-%02d %s | %s | answer=%s' % (
        i+1, qq['person_id'][:20], b['year'], b['month'], b['day'],
        qq['gender'][:1], qq['question'][:40], qq['answer'])
    print(out)

# Save
with open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=1)
print('\nsaved bench2021_questions.json')
