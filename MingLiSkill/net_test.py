# -*- coding: utf-8 -*-
"""Test local network access to corpus sources."""
import io, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
TESTS = [
    ('wikisource', 'https://zh.wikisource.org/zh-hans/%E6%BB%B4%E5%A4%A9%E9%AB%93%E9%97%A1%E5%BE%AE'),
    ('gushiwen', 'https://www.gushiwen.cn/gushi/tonghui.aspx'),
    ('github_raw', 'https://raw.githubusercontent.com/torvalds/linux/master/README'),
    ('github_api', 'https://api.github.com/search/repositories?q=%E6%B8%8A%E6%B5%B7%E5%AD%90%E5%B9%B3&per_page=5'),
]
out = []
for name, url in TESTS:
    try:
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(2000)
            out.append('%s: OK %d bytes | head: %s' % (name, len(body), body[:120]))
    except Exception as e:
        out.append('%s: FAIL %s' % (name, e))
with open(r'E:\ming_li_skill\MingLiSkill\net_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(out))
print('done')
