# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from extra_tools import SIHUA, sihua_feigong

out = []
out.append('SIHUA keys: %s' % list(SIHUA.keys()))
out.append('SIHUA[甲]: %s' % json.dumps(SIHUA.get('甲', 'NOT FOUND'), ensure_ascii=False))

palaces = {
    '子女': ['廉贞', '天相'], '夫妻': ['破军', '文昌'],
    '财帛': ['武曲', '天府'], '官禄': ['太阳', '文曲'],
}
out.append('palaces: %s' % json.dumps(palaces, ensure_ascii=False))

# Manual check
sihua = SIHUA.get('甲', {})
out.append('sihua for 甲: %s' % json.dumps(sihua, ensure_ascii=False))
for hua_type in ('禄', '权', '科', '忌'):
    star = sihua.get(hua_type)
    out.append('  %s -> star=%r' % (hua_type, star))
    if star:
        for palace, stars in palaces.items():
            found = star in stars
            out.append('    %s contains %r: %s' % (palace, star, found))

r = sihua_feigong('甲', palaces)
out.append('result: %s' % json.dumps(r, ensure_ascii=False))

with open(r'E:\ming_li_skill\MingLiSkill\debug_sihua.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
