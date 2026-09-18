# -*- coding: utf-8 -*-
"""Download all useful text files from china-testing/bazi + other sources."""
import io, sys, os, json, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0'}
DEST = r'E:\ming_li_skill\MingLiSkill\books'
os.makedirs(DEST, exist_ok=True)

REPO = 'china-testing/bazi'
FILES = [
    'books/zipingzhenquan.md',
    'books/zipingzhenquanjizhu.md',
    'books/穷通宝鉴.md',
    'examples/guan.md',
    'examples/shangguan.md',
    'examples/cai.md',
    'examples/pianguan.md',
    'examples/examples.md',
    'datas.py',
]

ok = fail = 0
total_bytes = 0
for path in FILES:
    raw = 'https://raw.githubusercontent.com/%s/HEAD/%s' % (REPO, urllib.parse.quote(path))
    try:
        req = urllib.request.Request(raw, headers=HDR)
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
        safe = path.replace('/', '__')
        with open(os.path.join(DEST, safe), 'wb') as f:
            f.write(body)
        total_bytes += len(body)
        ok += 1
        print('OK  %7d  %s' % (len(body), path))
    except Exception as e:
        fail += 1
        print('FAIL %s: %s' % (path, e))

# Also download 子平真诠 from litfresh/ziping-zhenquan
try:
    url = 'https://api.github.com/repos/litfresh/ziping-zhenquan/git/trees/HEAD?recursive=1'
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    for t in d.get('tree', []):
        if t['type'] == 'blob' and t['path'].endswith('.md') and t.get('size', 0) > 5000:
            raw = 'https://raw.githubusercontent.com/litfresh/ziping-zhenquan/HEAD/%s' % urllib.parse.quote(t['path'])
            req = urllib.request.Request(raw, headers=HDR)
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
            safe = 'ziping-zhenquan__' + t['path'].replace('/', '__')
            with open(os.path.join(DEST, safe), 'wb') as f:
                f.write(body)
            total_bytes += len(body)
            ok += 1
            print('OK  %7d  ziping-zhenquan/%s' % (len(body), t['path']))
except Exception as e:
    print('ziping-zhenquan FAIL: %s' % e)

# 千里命稿 from x3747991-ship-it repos (they have skill packs with book content)
try:
    url = 'https://api.github.com/repos/x3747991-ship-it/mingxue-zhendian/git/trees/HEAD?recursive=1'
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    for t in d.get('tree', []):
        if t['type'] == 'blob' and t['path'].endswith('.md') and t.get('size', 0) > 10000:
            raw = 'https://raw.githubusercontent.com/x3747991-ship-it/mingxue-zhendian/HEAD/%s' % urllib.parse.quote(t['path'])
            req = urllib.request.Request(raw, headers=HDR)
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
            safe = 'mingxue__' + t['path'].replace('/', '__')
            with open(os.path.join(DEST, safe), 'wb') as f:
                f.write(body)
            total_bytes += len(body)
            ok += 1
            print('OK  %7d  mingxue/%s' % (len(body), t['path']))
except Exception as e:
    print('mingxue FAIL: %s' % e)

print('\nTotal: ok=%d fail=%d bytes=%d (%.1f KB)' % (ok, fail, total_bytes, total_bytes/1024))
