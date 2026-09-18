# -*- coding: utf-8 -*-
"""
blind_school.py — 盲派八字工具
核心：弃旺衰、废用忌、专看结构与做功。
三大法则：理法（生克制化）、象法（类象直读）、技法（组合断）。
"""
from collections import defaultdict

# ============ 宾主分类 ============
# 年月 = 宾（外、他人、先天）；日时 = 主（内、自己、后天）
def classify_guest_host(pillars):
    return {
        '宾': [pillars.get('年柱',''), pillars.get('月柱','')],
        '主': [pillars.get('日柱',''), pillars.get('时柱','')],
    }

# ============ 体用分类（十神角度） ============
# 体 = 帮我/生我的（比劫、印）; 用 = 我克/克我的（财、官、食伤）
def classify_ti_yong(day_gan, ten_gods):
    ti = []  # 体: 帮身/生身
    yong = []  # 用: 耗/克/泄
    wx_self = {'木':'木','火':'火','土':'土','金':'金','水':'水'}[day_wx_map[day_gan]]
    for pos, ss in ten_gods.items():
        if ss in ('比肩','劫财','正印','偏印'):
            ti.append((pos, ss))
        elif ss in ('正财','偏财','正官','七杀','食神','伤官'):
            yong.append((pos, ss))
    return {'体': ti, '用': yong}

day_wx_map = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
    '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'
}

# ============ 做功类型 ============
GONG_TYPES = {
    '食神制杀': {'条件': ['食神', '七杀'], '断语': '靠技能权谋制伏压力，事业有成，权威之命', '关键词': ['事业有成','权威','技能','管理']},
    '伤官合杀': {'条件': ['伤官', '七杀'], '断语': '才华制伏暴力，化敌为友，逆境成器', '关键词': ['逆境','才华','化解']},
    '杀印相生': {'条件': ['七杀', '正印'], '断语': '压力化为学问，贵人提携，权威学者', '关键词': ['贵人','学术','权威','提携']},
    '财生杀攻身': {'条件': ['正财', '七杀'], '断语': '因财惹祸，钱生压力，防因财致灾', '关键词': ['因财','祸','压力','债务']},
    '伤官见官': {'条件': ['伤官', '正官'], '断语': '冒犯上级/法律，口舌官非，婚姻不顺', '关键词': ['官非','口舌','离婚','冒犯']},
    '枭神夺食': {'条件': ['偏印', '食神'], '断语': '夺走福气/子女缘，健康受损', '关键词': ['健康','子','损失']},
    '比劫夺财': {'条件': ['比肩', '正财'], '断语': '朋友/兄弟劫财，合作破财', '关键词': ['破财','被骗','朋友','合作']},
    '羊刃驾杀': {'条件': ['劫财', '七杀'], '断语': '以勇武制敌，武职权威，风险中成就', '关键词': ['武职','风险','勇','权威']},
    '财星坏印': {'条件': ['正财', '正印'], '断语': '贪财损名誉/学业，因小失大', '关键词': ['贪','损失','学业']},
    '官印双全': {'条件': ['正官', '正印'], '断语': '官印相生，仕途顺利，有地位有学问', '关键词': ['仕途','地位','学问','公职']},
    '食神生财': {'条件': ['食神', '正财'], '断语': '技艺生财，凭本事赚钱', '关键词': ['技艺','赚钱','生意','才华']},
    '伤官生财': {'条件': ['伤官', '偏财'], '断语': '创意生财，靠才能致富', '关键词': ['创意','才能','富','创新']},
}


def analyze_gong(ten_gods, wx_scores):
    """分析命局做功方式。
    ten_gods: {'年干': '正财', '月干': '七杀', ...} 全部十神位置
    wx_scores: {'正财': 2.5, '七杀': 1.0, ...} 十神对应五行力量
    返回: [(做功类型, 断语, 效率评分, 关键词)]"""
    # 收集存在的十神
    present = set()
    for pos, ss in ten_gods.items():
        present.add(ss)
    
    results = []
    for gong_name, gong_data in GONG_TYPES.items():
        conditions = gong_data['条件']
        # 检查条件十神是否都存在
        if all(c in present for c in conditions):
            # 计算效率：制方力量 / 被制方力量
            maker = conditions[0]
            target = conditions[1]
            maker_score = wx_scores.get(maker, 0)
            target_score = wx_scores.get(target, 0)
            efficiency = maker_score / max(target_score, 0.1)
            
            # 判断做功是否成功
            if efficiency > 1.2:
                status = '做功有力（成）'
            elif efficiency > 0.8:
                status = '做功中和（半成）'
            else:
                status = '做功无力（败）'
            
            results.append({
                '做功': gong_name,
                '断语': gong_data['断语'],
                '效率': round(efficiency, 2),
                '状态': status,
                '关键词': gong_data['关键词'],
            })
    
    # 按效率排序
    results.sort(key=lambda x: -x['效率'])
    return results


# ============ 象法直读 ============
# 天干类象
GAN_XIANG = {
    '甲': '头、大树、栋梁、领袖、开始',
    '乙': '颈、毛发、花草、藤萝、柔韧',
    '丙': '肩、太阳、影视、火、光明',
    '丁': '心、灯火、文字、香火、文明',
    '戊': '胃、城墙、堤坝、地产、厚重',
    '己': '脾、田园、平原、包容、滋养',
    '庚': '大肠、刀剑、矿石、刚硬、变革',
    '辛': '肺、珠玉、精细、金融、柔金',
    '壬': '膀胱、江河、流动、智慧、贸易',
    '癸': '肾、雨露、暗流、渗透、智谋',
}

# 地支类象
ZHI_XIANG = {
    '子': '耳、肾、鼠、暗、夜、贼、井',
    '丑': '腹、脾、牛、矿、金库、牢狱',
    '寅': '胆、虎、大树、驿马、道路、公门',
    '卯': '肝、兔、床、车船、门户、手',
    '辰': '皮肤、龙、水库、网、天罗、医',
    '巳': '面、蛇、炉冶、道路、文艺',
    '午': '眼、马、文书、信息、大火',
    '未': '脾、羊、林园、酒器、木库',
    '申': '大肠、猴、道路、金石、驿马',
    '酉': '肺、鸡、金银、酒、刀、精细',
    '戌': '腿、狗、火库、窑炉、庙宇',
    '亥': '肾、猪、江河、暗水、厕所',
}

def xiangfa_read(pillars):
    """象法直读：把四柱按类象读成一个故事。"""
    story = []
    for pos in ('年柱', '月柱', '日柱', '时柱'):
        gz = pillars.get(pos, '')
        if len(gz) < 2:
            continue
        g, z = gz[0], gz[1]
        g_xiang = GAN_XIANG.get(g, '')
        z_xiang = ZHI_XIANG.get(z, '')
        story.append('%s(%s=%s; %s=%s)' % (pos, g, g_xiang[:20], z, z_xiang[:20]))
    return story


# ============ 虚实判定 ============
def xu_shi_check(ten_gods, pillars):
    """检查哪些十神是实透（有根）vs 虚透（无根）。"""
    # 收集地支藏干
    hidden = set()
    from tools.calendar_engine import ZHI_CANG_GAN
    for pos in ('年柱', '月柱', '日柱', '时柱'):
        zhi = pillars.get(pos, '')[1:]
        if zhi:
            for g in ZHI_CANG_GAN.get(zhi, []):
                hidden.add(g)
    
    result = {'实透': [], '虚透': [], '藏': []}
    for pos, ss in ten_gods.items():
        if not pos.endswith('天干'):
            continue
        gan = pos.replace('天干', '')
        # 该十神对应的天干
        day_gan = ten_gods.get('日主', '甲')
        from tools.calendar_engine import TIANGAN
        for g in TIANGAN:
            from tools.calendar_engine import shi_shen
            if shi_shen(day_gan, g) == ss:
                if g in hidden:
                    result['实透'].append((pos, ss, g))
                else:
                    result['虚透'].append((pos, ss, g))
    
    return result
