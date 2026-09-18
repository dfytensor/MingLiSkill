# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'E:\ming_li_skill\MingLiSkill\wealth_fix.py'
c = open(p, encoding='utf-8').read()

old = """        year_zhi = pillars.get('年柱','')[1:2]
        has_wealth_in_year = False
        if year_zhi and ZHI_HIDE.get(year_zhi):
            for hg in ZHI_HIDE[year_zhi]:
                if GAN_WX.get(hg) == wealth_wx:
                    has_wealth_in_year = True
        rich_kw = ['富', '有钱']
        poor_kw = ['贫', '穷']
        if has_wealth_in_year:
            for o in opts:
                if any(k in o['text'] for k in ['富']) and '贫穷' not in o['text']:
                    pick = o['letter']; why = 'W1:年支%s藏财星→富' % year_zhi; break
        else:
            for o in opts:
                if '贫穷' in o['text'] or ('贫' in o['text'] and '富' not in o['text']):
                    pick = o['letter']; why = 'W1:年支%s无财星→贫' % year_zhi; break"""

new = """        year_zhi = pillars.get('年柱','')[1:2]
        benqi = ZHI_HIDE.get(year_zhi, (None,))[0]
        has_wealth_benqi = GAN_WX.get(benqi) == wealth_wx
        if has_wealth_benqi:
            for o in opts:
                if any(k in o['text'] for k in ['富', '有钱']) and '贫穷' not in o['text']:
                    pick = o['letter']; why = 'W1r:年支%s本气%s=财星→富' % (year_zhi, benqi); break
        # (贫分支已移除: 本气非财星不足以判贫, ftb_0081/0146 教训)"""

assert old in c, 'W1 block not found'
c = c.replace(old, new)
open(p, 'w', encoding='utf-8').write(c)
print('W1 refined OK')
