# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

p = r'E:\ming_li_skill\MingLiSkill\blind2021_run.py'
c = open(p, encoding='utf-8').read()

old = """        # C3
        if strong and any(k in alltxt for k in ['生意','事业','公司']):
            if ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == guan_wx:
                for o in opts:
                    if any(k in o['text'] for k in ['蒸蒸日上','峰回路转','好机遇','得奖','顺利','升']):
                        return o['letter'], 'C3:%s官本气+身强→事业好' % gz
    return None, 'no signal'"""

new = """        # C3
        if strong and any(k in alltxt for k in ['生意','事业','公司']):
            if ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == guan_wx:
                for o in opts:
                    if any(k in o['text'] for k in ['蒸蒸日上','峰回路转','好机遇','得奖','顺利','升']):
                        return o['letter'], 'C3:%s官本气+身强→事业好' % gz
        # X1: 七杀透干年 + 伤病 → 手术/住院 (古典: 杀主病伤)
        if ss_g == '七杀':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['开刀','住院','手术','伤'])), None)
            if cand: return cand, 'X1:%s七杀透→伤病' % gz
        # X2: 正官透干年 + 官非 → 官非 (古典: 官星动=见官)
        if ss_g == '正官':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['官非','牢狱','警察','扣留','犯法'])), None)
            if cand: return cand, 'X2:%s官透→官非' % gz
        # X3: 偏印年 + 投资/生意 → 失利/不顺 (枭神夺食)
        if ss_g == '偏印':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['失利','损失','不顺','赚不到钱','负债','停滞','失败'])), None)
            if cand: return cand, 'X3:%s偏印→停滞失利' % gz
        # X4: 劫财透干年 + 耗财 (古典: 劫财主破耗)
        if ss_g == '劫财':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['耗财','损失','失利','负债','赚不到钱'])), None)
            if cand: return cand, 'X4:%s劫财→破耗' % gz
        # X5: 伤官年 + 小财 (伤官生财)
        if ss_g == '伤官':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['赚得小财','小财','平中见顺'])), None)
            if cand: return cand, 'X5:%s伤官→技能小财' % gz
    return None, 'no signal'"""

assert old in c, 'X-block anchor missing'
c = c.replace(old, new)
open(p, 'w', encoding='utf-8').write(c)

# patch marriage_fix_v3: 二婚 wedding flag
p2 = r'E:\ming_li_skill\MingLiSkill\marriage_fix_v3.py'
c2 = open(p2, encoding='utf-8').read()
old2 = "is_wed = any(k in alltxt for k in ['结婚','結婚','成婚','娶','嫁'])"
new2 = "is_wed = any(k in alltxt for k in ['结婚','結婚','成婚','娶','嫁','二婚','再婚','第二婚','第二次结婚'])"
assert old2 in c2, 'wed-flag anchor missing'
c2 = c2.replace(old2, new2)
open(p2, 'w', encoding='utf-8').write(c2)
print('patched X signals + er-hun flag OK')
