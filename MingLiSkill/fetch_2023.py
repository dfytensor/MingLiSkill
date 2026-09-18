# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

# 2023年6月 题目发布帖
h = get_page('2023/06/由香港青年術數家協會主辦-2023年第十四屆全球算命師大賽')
imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/2023/0[56][^"]+\.jpg)"', h)
seen = []
for u in imgs:
    if u not in seen and '-766x' not in u:
        seen.append(u)
print('2023 question page imgs:', len(seen))
open(r'E:\ming_li_skill\MingLiSkill\data2020\q2023_urls.txt', 'w', encoding='utf-8').write('\n'.join(seen))

# download answer images (full size) + question images
downloads = [
    ('https://hkjfma.org/wp-content/uploads/2023/09/365544242_10226968184404187_317874141709423254_n.jpg', 'ans2023_0.jpg'),
    ('https://hkjfma.org/wp-content/uploads/2023/09/367708265_10227006713327386_8653851229976436861_n-1.jpg', 'ans2023_1.jpg'),
    ('https://hkjfma.org/wp-content/uploads/2023/09/367694853_10227006713767397_5927952724709152324_n.jpg', 'ans2023_2.jpg'),
    ('https://hkjfma.org/wp-content/uploads/2023/09/367709173_10227006713487390_2402161550757507200_n.jpg', 'ans2023_3.jpg'),
]
for i, u in enumerate(seen[:12]):
    downloads.append((u, 'q2023_%d.jpg' % i))

for u, fn in downloads:
    out = r'E:\ming_li_skill\MingLiSkill\data2020' + chr(92) + fn
    subprocess.run(['curl', '-s', '-L', '-o', out, '--max-time', '90', u], capture_output=True)
    print('got', fn)
