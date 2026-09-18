# -*- coding: utf-8 -*-
"""Fetch MingLi-Bench repo info + methodology page."""
import io, sys, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'}

out = []
# 1) Repo README
try:
    url = 'https://api.github.com/repos/DestinyLinker/MingLi-Bench/readme'
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    import base64
    content = base64.b64decode(d['content']).decode('utf-8')
    out.append('=== README (%d chars) ===' % len(content))
    out.append(content[:8000])
except Exception as e:
    out.append('README FAIL: %s' % e)

# 2) File tree
try:
    url = 'https://api.github.com/repos/DestinyLinker/MingLi-Bench/git/trees/HEAD?recursive=1'
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    out.append('\n=== FILES ===')
    for t in d.get('tree', []):
        if t['type'] == 'blob':
            out.append('  %7d  %s' % (t.get('size', 0), t['path']))
except Exception as e:
    out.append('TREE FAIL: %s' % e)

with open(r'E:\ming_li_skill\MingLiSkill\bench_info.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done, %d lines' % len(out))
