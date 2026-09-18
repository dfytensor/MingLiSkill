# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re, sys

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

def extract_imgs(html, year_prefix='20'):
    # find both src= and href= image links
    imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/[^"]+\.jpg)"', html)
    seen = []
    for u in imgs:
        if u not in seen:
            seen.append(u)
    return seen

out = []

# 2018 题目页
h1 = get_page('過往活動/2018第九屆算命比賽題目')
i1 = extract_imgs(h1)
out.append('2018 questions page imgs: %d' % len(i1))
out += i1

# 2018 答案页
h2 = get_page('過往活動/2018第九屆算命比賽題目/2018第九屆全球算命師比賽答案及得獎名單')
i2 = extract_imgs(h2)
out.append('2018 answer page imgs: %d' % len(i2))
out += i2

# 2019 答案页
h3 = get_page('過往活動/2019第十屆全球算命師比賽/2019年度第十屆全球算命師比賽答案,得獎名單及統計資料'.replace(',', ','))
i3 = extract_imgs(h3)
out.append('2019 answer page imgs: %d' % len(i3))
out += i3

# 2023 答案页 (from earlier fetch: 4 imgs)
h4 = get_page('2023/09/2023年第十四屆全球算命師大賽答案及得獎名單')
i4 = extract_imgs(h4)
out.append('2023 answer page imgs: %d' % len(i4))
out += i4

open(r'E:\ming_li_skill\MingLiSkill\data2020\all_image_urls.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:3]))
print('total lines:', len(out))
