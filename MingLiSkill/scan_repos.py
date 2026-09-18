# -*- coding: utf-8 -*-
"""Fetch file trees of candidate corpus repos."""
import io, sys, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0'}
REPOS = [
    'workhardooday/Bazi_RAG_Agent',
    'henrryjoke/diguan-bazi',
    'HunterTree/ditiansui',
    'secret04725-coder/bazi-master-skill',
    'x3747991-ship-it/ditiansui-skillpack',
    'x3747991-ship-it/mingxue-zhendian',
]
out = []
for repo in REPOS:
    try:
        url = 'https://api.github.com/repos/%s/git/trees/HEAD?recursive=1' % repo
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode('utf-8'))
        files = [(t['path'], t.get('size', 0)) for t in d.get('tree', []) if t['type'] == 'blob']
        big = [(p, s) for p, s in files if any(p.endswith(e) for e in ('.txt', '.md', '.json')) and s > 3000]
        out.append('== %s: %d files ==' % (repo, len(files)))
        for p, s in sorted(big, key=lambda x: -x[1])[:15]:
            out.append('  %6d  %s' % (s, p))
    except Exception as e:
        out.append('== %s FAIL %s ==' % (repo, e))
with open(r'E:\ming_li_skill\MingLiSkill\repo_trees.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
