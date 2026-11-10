# -*- coding: utf-8 -*-
"""
渐进交付策略的最终答案取值脚本。

输入：测评结果文件（Excel或CSV），每行一条测评数据，需包含两列：
    promptOut   ：知识库输出结果
    skillResult ：技能输出结果

取值逻辑（按优先级）：
    1) 技能输出结果存在                         -> 取技能输出结果（不论知识库是否有答案）
    2) 技能输出结果不存在，知识库输出结果存在     -> 取知识库输出结果
    3) 两者都不存在                              -> 取"未检索到答案"

"不存在"的判定（按"包含"匹配，不要求完全一致）：
    知识库输出结果：空值、空白字符串，或包含"未检索到答案"、"未检索到相关信息"
    技能输出结果  ：空值、空白字符串，或包含"Agent执行异常"、"NO_SKILL_MATCHED"（不区分大小写）

输出：在原有列基础上新增两列，写入新的Excel文件：
    最终答案  ：按上述逻辑取到的答案
    答案来源  ：技能 / 知识库 / 无答案

用法：
    python3 select_progressive_answer.py <输入文件> [--sheet SHEET] [--output 输出路径]
                                          [--kb-col promptOut] [--skill-col skillResult]
"""

import argparse
import sys

import pandas as pd

NO_ANSWER_TEXT = '未检索到答案'

KB_INVALID_KEYWORDS = (NO_ANSWER_TEXT, '未检索到相关信息')
SKILL_INVALID_KEYWORDS = ('Agent执行异常', 'NO_SKILL_MATCHED')

SOURCE_SKILL = '技能'
SOURCE_KB = '知识库'
SOURCE_NONE = '无答案'


def _normalize(value):
    """转成去掉首尾空白的字符串；空值返回空字符串。"""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ''
    return str(value).strip()


def _contains_any(text, keywords):
    upper_text = text.upper()
    return any(k.upper() in upper_text for k in keywords)


def has_kb_answer(value):
    text = _normalize(value)
    return text != '' and not _contains_any(text, KB_INVALID_KEYWORDS)


def has_skill_answer(value):
    text = _normalize(value)
    return text != '' and not _contains_any(text, SKILL_INVALID_KEYWORDS)


def select_answer(kb_output, skill_output):
    """返回 (最终答案, 答案来源)。"""
    if has_skill_answer(skill_output):
        return str(skill_output).strip(), SOURCE_SKILL
    if has_kb_answer(kb_output):
        return str(kb_output).strip(), SOURCE_KB
    return NO_ANSWER_TEXT, SOURCE_NONE


def load_table(path, sheet=0):
    if str(path).lower().endswith('.csv'):
        return pd.read_csv(path)
    return pd.read_excel(path, sheet_name=sheet)


def main():
    parser = argparse.ArgumentParser(description='渐进交付策略最终答案取值脚本')
    parser.add_argument('input', help='测评结果文件路径（xlsx/xls/csv）')
    parser.add_argument('--sheet', default=0, help='Excel的sheet名或索引，默认第一个sheet')
    parser.add_argument('--output', default='progressive_answer_selected.xlsx', help='输出Excel路径')
    parser.add_argument('--kb-col', default='promptOut', help='知识库输出结果所在列名')
    parser.add_argument('--skill-col', default='skillResult', help='技能输出结果所在列名')
    args = parser.parse_args()

    df = load_table(args.input, args.sheet)
    missing = [c for c in (args.kb_col, args.skill_col) if c not in df.columns]
    if missing:
        raise ValueError(f'输入文件缺少字段：{missing}；现有字段：{list(df.columns)}')

    picked = df.apply(lambda row: select_answer(row[args.kb_col], row[args.skill_col]), axis=1)
    df['最终答案'] = [p[0] for p in picked]
    df['答案来源'] = [p[1] for p in picked]

    df.to_excel(args.output, index=False)

    total = len(df)
    print(f'总行数：{total}')
    for source in (SOURCE_SKILL, SOURCE_KB, SOURCE_NONE):
        n = int((df['答案来源'] == source).sum())
        pct = n / total * 100 if total else 0
        print(f'取值来源={source}：{n}（{pct:.1f}%）')
    print(f'结果已写入：{args.output}')


if __name__ == '__main__':
    sys.exit(main())
