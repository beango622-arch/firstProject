# -*- coding: utf-8 -*-
"""
渐进交付策略最终答案取值（工作流Python节点版，仅依赖标准库）。

输入变量：
    promptOut   ：知识库输出结果
    skillResult ：技能输出结果

取值逻辑（按优先级）：
    1) 技能输出结果存在                       -> 取技能输出结果
    2) 技能不存在，知识库输出结果存在           -> 取知识库输出结果
    3) 两者都不存在                            -> 取"未检索到答案"

"不存在"的判定（按"包含"匹配）：
    知识库：空值、空白字符串，或包含"未检索到答案"、"未检索到相关信息"
    技能  ：空值、空白字符串，或包含"Agent执行异常"、"NO_SKILL_MATCHED"（不区分大小写）

输出变量：
    finalAnswer  ：最终答案
    answerSource ：技能 / 知识库 / 无答案
"""

NO_ANSWER_TEXT = '未检索到答案'
KB_INVALID_KEYWORDS = (NO_ANSWER_TEXT, '未检索到相关信息')
SKILL_INVALID_KEYWORDS = ('Agent执行异常', 'NO_SKILL_MATCHED')


def _normalize(value):
    if value is None:
        return ''
    return str(value).strip()


def _contains_any(text, keywords):
    upper_text = text.upper()
    return any(k.upper() in upper_text for k in keywords)


def main(promptOut=None, skillResult=None):
    kb_text = _normalize(promptOut)
    skill_text = _normalize(skillResult)

    if skill_text and not _contains_any(skill_text, SKILL_INVALID_KEYWORDS):
        return {'finalAnswer': skill_text, 'answerSource': '技能'}
    if kb_text and not _contains_any(kb_text, KB_INVALID_KEYWORDS):
        return {'finalAnswer': kb_text, 'answerSource': '知识库'}
    return {'finalAnswer': NO_ANSWER_TEXT, 'answerSource': '无答案'}
