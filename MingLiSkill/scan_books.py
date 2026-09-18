# -*- coding: utf-8 -*-
"""Download mingli books from GitHub china-testing/bazi repo + quanxue.cn."""
import io, sys, os, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0'}
DEST = r'E:\ming_li_skill\MingLiSkill\books'
os.makedirs(DEST, exist_ok=True)

# 1) Get file tree of china-testing/bazi
try:
    url = 'https://api.github.com/repos/china-testing/bazi/git/trees/HEAD?recursive=1'
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    files = [(t['path'], t.get('size', 0)) for t in d.get('tree', []) if t['type'] == 'blob']
    # Show all files > 1KB
    out = ['=== china-testing/bazi: %d files ===' % len(files)]
    for p, s in sorted(files, key=lambda x: -x[1]):
        if s > 500:
            out.append('  %8d  %s' % (s, p))
except Exception as e:
    out.append('bazi repo FAIL: %s' % e)

# 2) Check quanxue.cn 千里命稿 chapters
try:
    url = 'https://www.quanxue.cn/ls_QianLi/QianLi.html'
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    import re
    links = re.findall(r'href=[\'"]([^\'"]*QianLi[^\'"]*)[\'"][^>]*>([^<]+)<', html)
    out.append('\n=== quanxue.cn 千里命稿 chapters: %d ===' % len(links))
    for u, t in links[:30]:
        out.append('  %s %s' % (u, t.strip()))
except Exception as e:
    out.append('\nquanxue FAIL: %s' % e)

with open(r'E:\ming_li_skill\MingLiSkill\books_scan.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
