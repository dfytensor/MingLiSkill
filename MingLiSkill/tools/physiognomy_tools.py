from __future__ import annotations

import json
from typing import Dict, List, Optional

from .toolkit_base import Toolkit


FACE_TWELVE_PALACES = {
    "命宫": {"位置": "两眉之间（印堂）", "主": "一生运势、性格、愿望"},
    "财帛宫": {"位置": "鼻子", "主": "财运、理财能力"},
    "兄弟宫": {"位置": "眉毛", "主": "兄弟朋友关系"},
    "夫妻宫": {"位置": "眼尾（奸门）", "主": "婚姻感情"},
    "子女宫": {"位置": "下眼睑（泪堂）", "主": "子女缘分"},
    "疾厄宫": {"位置": "山根至鼻梁", "主": "健康灾厄"},
    "迁移宫": {"位置": "额角（天仓）", "主": "出行、变动"},
    "仆役宫": {"位置": "地阁（下巴两侧）", "主": "下属、朋友"},
    "官禄宫": {"位置": "额头正中", "主": "事业地位"},
    "田宅宫": {"位置": "眉眼之间（上眼睑）", "主": "不动产、家庭"},
    "福德宫": {"位置": "眉尾上方（天仓）", "主": "福气、精神"},
    "父母宫": {"位置": "日月角（额头上方左右）", "主": "父母、长辈"},
}

FIVE_ORGANS_WUXING = {
    "眼": {"五行": "木", "对应脏腑": "肝", "相理": "眼为监察官，黑白分明为佳"},
    "舌": {"五行": "火", "对应脏腑": "心", "相理": "舌为审辨官，红润灵活为佳"},
    "口": {"五行": "土", "对应脏腑": "脾", "相理": "口为出纳官，方阔红润为佳"},
    "鼻": {"五行": "金", "对应脏腑": "肺", "相理": "鼻为审辨官，丰隆挺直为佳"},
    "耳": {"五行": "水", "对应脏腑": "肾", "相理": "耳为采听官，厚大轮廓分明为佳"},
}

PALM_THREE_LINES = {
    "生命线": {"又名": "地纹", "位置": "拇指与食指之间弧形延伸至手腕", "主": "生命力、健康、活力"},
    "智慧线": {"又名": "人纹", "位置": "食指与拇指之间横贯掌心", "主": "智力、思维、才华"},
    "感情线": {"又名": "天纹", "位置": "小指下方横贯至食指", "主": "感情、婚姻、人际关系"},
}

PALM_AUX_LINES = {
    "事业线": {"又名": "命运线", "位置": "手腕中线上延至中指", "主": "事业发展"},
    "太阳线": {"又名": "成功线", "位置": "无名指下方竖线", "主": "名誉、成功"},
    "健康线": {"又名": "肝脏线", "位置": "感情线与生命线之间斜线", "主": "健康状况"},
    "婚姻线": {"又名": "爱情线", "位置": "小指与感情线之间横线", "主": "婚姻"},
    "财运线": {"位置": "无名指与小指之间竖线", "主": "财运"},
}

FACE_FIVE_MOUNTAINS = {
    "南岳": {"位置": "额头", "对应": "官禄、早年运"},
    "北岳": {"位置": "地阁（下巴）", "对应": "晚年运"},
    "东岳": {"位置": "左颧", "对应": "权力、人际关系"},
    "西岳": {"位置": "右颧", "对应": "权力、人际关系"},
    "中岳": {"位置": "鼻子", "对应": "财帛、中年运"},
}

FACE_THREE_STOPS = {
    "上停": {"范围": "发际至眉毛", "主": "早年运（15-30岁）", "代表": "天"},
    "中停": {"范围": "眉毛至鼻尖", "主": "中年运（31-50岁）", "代表": "人"},
    "下停": {"范围": "鼻尖至下巴", "主": "晚年运（51岁后）", "代表": "地"},
}


class PhysiognomyToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.face_twelve_palaces,
            self.face_five_organs,
            self.face_three_stops,
            self.face_five_mountains,
            self.analyze_face_shape,
            self.palm_three_lines,
            self.palm_auxiliary_lines,
            self.analyze_finger_shape,
            self.mianxiang_jinju,
        ]
        super().__init__(name="physiognomy_tools", tools=tools, **kwargs)

    def face_twelve_palaces(self, palace_name: str = "") -> str:
        """
        面相十二宫：查询面相十二宫的位置和所主管的运势。

        Args:
            palace_name: 宫位名称 (如 "命宫", "财帛宫")。留空返回全部十二宫。
        """
        try:
            if palace_name:
                info = FACE_TWELVE_PALACES.get(palace_name)
                if not info:
                    return json.dumps({"success": False, "error": f"未找到 '{palace_name}'"}, ensure_ascii=False)
                return json.dumps({"success": True, "宫位": palace_name, **info}, ensure_ascii=False)
            return json.dumps({"success": True, "面相十二宫": FACE_TWELVE_PALACES}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def face_five_organs(self, organ: str = "") -> str:
        """
        面相五官：查询五官（眼、舌、口、鼻、耳）对应的五行和相理。

        Args:
            organ: 器官名称 (如 "眼", "鼻", "耳")。留空返回全部五官。
        """
        try:
            if organ:
                info = FIVE_ORGANS_WUXING.get(organ)
                if not info:
                    return json.dumps({"success": False, "error": f"未找到 '{organ}'"}, ensure_ascii=False)
                return json.dumps({"success": True, "器官": organ, **info}, ensure_ascii=False)
            return json.dumps({"success": True, "五官五行": FIVE_ORGANS_WUXING}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def face_three_stops(self) -> str:
        """
        面相三停：查询面相上中下三停的分法和代表的年龄段运势。无需参数。
        """
        return json.dumps({"success": True, "面相三停": FACE_THREE_STOPS}, ensure_ascii=False)

    def face_five_mountains(self) -> str:
        """
        面相五岳：查询面部五岳的位置和所代表的运势。无需参数。
        """
        return json.dumps({"success": True, "面相五岳": FACE_FIVE_MOUNTAINS}, ensure_ascii=False)

    def analyze_face_shape(self, shape: str) -> str:
        """
        面型分析：根据面型分析性格和运势倾向。

        Args:
            shape: 面型 ("圆形", "方形", "长形", "三角形", "鹅蛋形", "由字脸",
                         "甲字脸", "申字脸", "目字脸", "王字脸", "风字脸", "同字脸")
        """
        try:
            shape_info = {
                "圆形": {"五行": "水", "性格": "圆滑、善于社交、适应力强", "适合": "商界、交际"},
                "方形": {"五行": "金", "性格": "正直、务实、行动力强", "适合": "军警、管理"},
                "长形": {"五行": "木", "性格": "思考型、有远见、多虑", "适合": "学术、策划"},
                "三角形": {"五行": "火", "性格": "聪明、敏感、多才", "适合": "艺术、创新"},
                "鹅蛋形": {"五行": "木", "性格": "温和、有涵养、重感情", "适合": "文职、教育"},
                "由字脸": {"特征": "上窄下宽", "性格": "踏实、物质欲强、重家庭", "运势": "晚年运佳"},
                "甲字脸": {"特征": "上宽下窄", "性格": "理想主义、善于思考", "运势": "早年运佳"},
                "申字脸": {"特征": "中间窄两头宽", "性格": "双面性、善于应变", "运势": "中年波折"},
                "目字脸": {"特征": "长方", "性格": "稳重、有耐心", "运势": "平稳"},
                "风字脸": {"特征": "下颌宽大", "性格": "精力充沛、固执", "运势": "执行能力强"},
            }
            info = shape_info.get(shape)
            if not info:
                return json.dumps({"success": False, "error": f"未收录 '{shape}' 面型"}, ensure_ascii=False)
            return json.dumps({"success": True, "面型": shape, **info}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def palm_three_lines(self, line_name: str = "") -> str:
        """
        手相三大主线：查询生命线、智慧线、感情线的位置和含义。

        Args:
            line_name: 线名 ("生命线", "智慧线", "感情线")。留空返回全部。
        """
        try:
            if line_name:
                info = PALM_THREE_LINES.get(line_name)
                if not info:
                    return json.dumps({"success": False, "error": f"未找到 '{line_name}'"}, ensure_ascii=False)
                return json.dumps({"success": True, "掌纹": line_name, **info}, ensure_ascii=False)
            return json.dumps({"success": True, "三大主线": PALM_THREE_LINES}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def palm_auxiliary_lines(self, line_name: str = "") -> str:
        """
        手相辅助线：查询事业线、婚姻线、财运线等辅助线的含义。

        Args:
            line_name: 线名 ("事业线", "太阳线", "健康线", "婚姻线", "财运线")。留空返回全部。
        """
        try:
            if line_name:
                info = PALM_AUX_LINES.get(line_name)
                if not info:
                    return json.dumps({"success": False, "error": f"未找到 '{line_name}'"}, ensure_ascii=False)
                return json.dumps({"success": True, "掌纹": line_name, **info}, ensure_ascii=False)
            return json.dumps({"success": True, "辅助线": PALM_AUX_LINES}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_finger_shape(self, finger_type: str) -> str:
        """
        指型分析：根据手指形状分析性格特征。

        Args:
            finger_type: 指型 ("方形指", "尖形指", "圆锥指", "竹节指", "混合指")
        """
        try:
            finger_info = {
                "方形指": {"性格": "务实、条理、重秩序", "职业倾向": "管理、工程"},
                "尖形指": {"性格": "敏感、直觉强、理想主义", "职业倾向": "艺术、文学"},
                "圆锥指": {"性格": "直觉敏锐、善于表达", "职业倾向": "演讲、表演"},
                "竹节指": {"性格": "思考深刻、追求真理", "职业倾向": "哲学、研究"},
                "混合指": {"性格": "多面性、适应力强", "职业倾向": "综合型"},
            }
            info = finger_info.get(finger_type)
            if not info:
                return json.dumps({"success": False, "error": f"未收录 '{finger_type}'"}, ensure_ascii=False)
            return json.dumps({"success": True, "指型": finger_type, **info}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def mianxiang_jinju(self, part: str) -> str:
        """
        面相金句：查询面相各部位的经典相法口诀。

        Args:
            part: 部位 ("额", "眉", "眼", "鼻", "口", "耳", "颧", "下巴", "痣")
        """
        try:
            jinju = {
                "额": ["天庭饱满吃官饭，地阁方圆掌大权", "额头宽大主聪明，窄小平塌多艰辛"],
                "眉": ["眉清目秀主文才，眉粗浓密性刚强", "眉毛过眼兄弟多，短不过目半蹉跎"],
                "眼": ["眼如日月要分明，凤目朝天富贵荣", "眼大而有神者聪，眼小而长者精"],
                "鼻": ["鼻如截筒衣食丰，鼻如悬胆财帛充", "鼻梁低陷财帛少，鼻头丰圆家业兴"],
                "口": ["口方唇红食禄丰，口小唇薄多辛苦", "唇如涂朱主富贵，唇黑唇青多疾病"],
                "耳": ["耳大贴肉富贵足，耳高于眉聪明显", "耳薄无轮廓反贫，耳白于面名扬天下"],
                "颧": ["颧高权大贵人相，颧低无权多操劳", "女子颧高杀夫星，男子颧高权柄重"],
                "下巴": ["地阁方圆晚运好，尖削短薄老来穷", "下巴丰满主有福，双下巴主安享晚年"],
                "痣": ["面无善痣方为贵，痣在隐处反为吉", "额头主贵下巴主富，鼻头主财眼尾主桃花"],
            }
            sayings = jinju.get(part)
            if not sayings:
                return json.dumps({"success": False, "error": f"未收录 '{part}'"}, ensure_ascii=False)
            return json.dumps({"success": True, "部位": part, "相法口诀": sayings}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
