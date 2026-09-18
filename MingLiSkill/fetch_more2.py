# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

def links_and_imgs(html, base='wp-content/uploads'):
    found = re.findall(r'(?:src|href)="(http[^"]+' + base + r'/[^"]+\.(?:jpg|jpeg|png|pdf))"', html)
    seen = []
    for u in found:
        if u not in seen and 'logo' not in u and 'fb.jpg' not in u and '766x' not in u:
            seen.append(u)
    return seen

out = []

# 2023年6月帖子: 从答案页HTML里找链接
h4 = get_page('2023/09/2023年第十四屆全球算命師大賽答案及得獎名單')
allinks = re.findall(r'href="(https://hkjfma\.org/2023/0[67][^"]+)"', h4)
out.append('2023 answer page post-links:')
for u in allinks[:10]:
    out.append('  ' + u)

# 2019 第十屆主帖(可能含题目)
h5 = get_page('過往活動/2019第十屆全球算命師比賽/2019年度全球算命師比賽（第十屆）')
i5 = links_and_imgs(h5)
out.append('2019 main post imgs: %d' % len(i5))
out += ['  ' + u for u in i5[:15]]

# 2021 第十二屆主帖
h6 = get_page('過往活動/2021年第十二屆全球算命師大賽')
i6 = links_and_imgs(h6)
out.append('2021 main post imgs: %d' % len(i6))
out += ['  ' + u for u in i6[:15]]

# 2024 第十五屆
h7 = get_page('2024/05/2024年第十五屆-全球算命師比賽')
i7 = links_and_imgs(h7)
out.append('2024 post imgs: %d' % len(i7))
out += ['  ' + u for u in i7[:15]]

open(r'E:\ming_li_skill\MingLiSkill\data2020\more_pages.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out))
