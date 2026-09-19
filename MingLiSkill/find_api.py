# -*- coding: utf-8 -*-
import subprocess, re, json

r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', 'https://asklingxi.com/mingli-dasai/2019'], capture_output=True)
h = r.stdout.decode('utf-8', errors='replace')

apis = re.findall(r'["\'](/api/[^"\']+)["\']', h)
seen = []
for a in apis:
    if a not in seen:
        seen.append(a)
print('API endpoints:', len(seen))
for a in seen[:20]:
    print(' ', a)

# quiz 页测试
r2 = subprocess.run(['curl', '-s', '-L', '--max-time', '60', 'https://asklingxi.com/bazi/quiz/e10-c1'], capture_output=True)
h2 = r2.stdout.decode('utf-8', errors='replace')
print('quiz page size:', len(h2))
# 在 quiz 页找答案标记
for pat in ['correctAnswer', 'correct_answer', '"answer"', '官方', '正确答案']:
    cnt = h2.count(pat)
    print(pat, 'count:', cnt)
# 保存quiz页供检查
open(r'E:\ming_li_skill\MingLiSkill\data_archive\quiz_page.html', 'w', encoding='utf-8').write(h2)
