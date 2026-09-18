# -*- coding: utf-8 -*-
"""
data_extractor.py v2 — 修复版数据提取器
修复: gz_key拼接错误、有根检测、天干/地支藏干正确映射
"""
from tools.calendar_engine import ZHI_CANG_GAN, TIANGAN, shi_shen

def extract_shishen_detail(ten_gods, pillars, wx, day_gan):
    """输出完整十神分析，每种十神分别列出（不合并）。"""
    # 收集所有地支藏干
    hidden_gans = set()
    for p in ('年柱', '月柱', '日柱', '时柱'):
        z = pillars.get(p, '')[1:2]
        if z:
            for g in ZHI_CANG_GAN.get(z, []):
                hidden_gans.add(g)
    
    result = {}
    for pos, ss_name in ten_gods.items():
        if pos == '日主':
            continue
        
        # 解析位置
        pillar_name = None
        stem = None
        source = pos  # e.g. '年柱天干', '月柱地支本气'
        
        if '天干' in pos:
            pillar_name = pos.replace('天干', '')
            gz = pillars.get(pillar_name, '')
            stem = gz[0] if gz else None
        elif '地支' in pos:
            pillar_name = pos.replace('地支本气', '').replace('地支中气', '').replace('地支余气', '')
            gz = pillars.get(pillar_name, '')
            zhi = gz[1:2] if len(gz) > 1 else ''
            hidden = ZHI_CANG_GAN.get(zhi, [])
            if '本气' in pos:
                stem = hidden[0] if hidden else None
            elif '中气' in pos:
                stem = hidden[1] if len(hidden) > 1 else None
            elif '余气' in pos:
                stem = hidden[2] if len(hidden) > 2 else None
        
        if not stem:
            continue
        
        # 有根判断: 该天干是否出现在任何地支藏干中
        has_root = stem in hidden_gans
        
        # 五行
        from tools.calendar_engine import WUXING_GAN
        wuxing = WUXING_GAN.get(stem, '')
        
        result.setdefault(ss_name, []).append({
            '位置': pos,
            '天干': stem,
            '有根': has_root,
            '五行': wuxing,
            '透干': '天干' in pos,
        })
    
    return result


def extract_wuxing_balance(wx):
    """完整五行平衡报告（含脏腑映射）。"""
    total = sum(wx.values()) or 1
    result = {}
    organ_map = {'木': '肝胆/筋/目', '火': '心/小肠/血脉', '土': '脾胃/肌肉',
                 '金': '肺/大肠/皮毛', '水': '肾/膀胱/骨/耳'}
    for w, c in wx.items():
        pct = c / total * 100
        result[w] = {
            '力量': c,
            '占比': round(pct, 1),
            '脏腑': organ_map.get(w, ''),
            '状态': '缺' if pct == 0 else ('极旺' if pct > 40 else ('偏旺' if pct > 30 else ('正常' if pct >= 10 else '偏弱'))),
        }
    return result


def extract_gender_specific(ten_gods, gender, day_gan):
    """性别相关十神完整数据。"""
    female = gender in ('女', 'F', 'female')
    tg = {k: v for k, v in ten_gods.items() if k.endswith('天干')}
    
    result = {
        '性别': '女' if female else '男',
        '透干十神': list(set(tg.values())),
    }
    
    if female:
        # 女命: 官杀=丈夫, 食伤=子女+克官
        guan_positions = [(k, v) for k, v in ten_gods.items() if v in ('正官', '七杀')]
        shang_positions = [(k, v) for k, v in ten_gods.items() if v in ('伤官', '食神')]
        result['官杀(丈夫)'] = {
            '说明': '女命以正官为正夫、七杀为偏夫/情人',
            '位置': [{'位置': k, '十神': v} for k, v in guan_positions],
            '数量': len(guan_positions),
            '伤官(克官)位置': [{'位置': k, '十神': v} for k, v in shang_positions],
            '伤官数量': len(shang_positions),
            '结论数据': '官杀%d个 vs 伤官%d个' % (len(guan_positions), len(shang_positions)),
        }
        result['食伤(子女)'] = {
            '说明': '女命以食伤为子女',
            '数量': len(shang_positions),
        }
    else:
        # 男命: 财星=妻子, 食伤=子女(通过妻)
        cai_positions = [(k, v) for k, v in ten_gods.items() if v in ('正财', '偏财')]
        bijie_positions = [(k, v) for k, v in ten_gods.items() if v in ('比肩', '劫财')]
        result['财星(妻子)'] = {
            '说明': '男命以正财为正妻、偏财为偏妻/父亲',
            '位置': [{'位置': k, '十神': v} for k, v in cai_positions],
            '数量': len(cai_positions),
            '比劫(克财)数量': len(bijie_positions),
            '结论数据': '财星%d个 vs 比劫%d个' % (len(cai_positions), len(bijie_positions)),
        }
    
    return result


def extract_pillar_interactions(pillars):
    """干支关系全查。"""
    from advanced_tools import all_pillar_relations
    return all_pillar_relations(pillars)


def extract_star_combinations(ziwei_palace_data):
    """紫微每宫完整数据（含亮度、四化等所有字段）。"""
    result = {}
    for palace, data in ziwei_palace_data.items():
        if isinstance(data, dict):
            # 保留所有字段不省略
            result[palace] = data
    return result
