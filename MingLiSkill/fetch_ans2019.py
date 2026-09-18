# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re, os

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

base = r'E:\ming_li_skill\MingLiSkill\data2019' + chr(92)

# 2019 答案页 - 抓所有 uploads 图片不限路径
h = get_page('過往活動/2019第十屆全球算命師比賽/2019年度第十屆全球算命師比賽答案,得獎名單及統計資料')
imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png))"', h)
seen = []
for u in imgs:
    if u not in seen and 'logo' not in u and 'fb.jpg' not in u:
        seen.append(u)
print('2019 answer page ALL imgs:', len(seen))
for u in seen:
    print(' ', u)

for i, u in enumerate(seen):
    fn = 'ans2019_%d.jpg' % i
    subprocess.run(['curl', '-s', '-L', '-o', base + fn, '--max-time', '90', u], capture_output=True)
    print('got', fn)
