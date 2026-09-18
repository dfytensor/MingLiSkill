# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from extra_tools import sihua_feigong, star_brightness, auto_yongshen

# 四化飞星
palaces = {
    '子女': ['廉贞', '天相'], '夫妻': ['破军', '文昌'],
    '财帛': ['武曲', '天府'], '官禄': ['太阳', '文曲'],
}
r = sihua_feigong('甲', palaces)
out = ['四化飞星(甲): ' + json.dumps(r, ensure_ascii=False)]

# 星曜亮度
b, s = star_brightness('紫微', '午')
out.append('紫微在午: %s(%d)' % (b, s))
b, s = star_brightness('太阴', '卯')
out.append('太阴在卯: %s(%d)' % (b, s))

with open(r'E:\ming_li_skill\MingLiSkill\extra_tools_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
