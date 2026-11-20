# -*- coding: utf-8 -*-
"""咨询记录第一步清洗：按 用户ID + 会话ID 合并同一次会话的多行记录。

用法：
    python merge_consultation_sessions.py --input 咨询记录.xlsx --output 会话合并结果.xlsx

合并规则：
    拉起人工      组内任意一行为"是" → 是，否则 否
    Agent工作状态 组内出现 执行异常/NO_SKILL_MATCHED/正常（按此优先级）→ 取该值，否则 未进行技能检索
    Rag工作状态   组内出现 正常/未检索到相关信息（按此优先级）→ 取该值，否则 未进行知识库检索
    Doc工作状态   组内出现 执行异常/NO_DOC_MATCHED/正常（按此优先级）→ 取该值，否则 未进行文档检索
    会话开始时间  取组内最早时间；用户问题取最早一条非空；用户姓名取第一个非空
    回答答案      组内非空且不重复的答案按换行拼接
    会话ID或用户ID缺失的行无法合并，各自单独成行
"""
import argparse
import sys

import pandas as pd

COL_SESSION = '会话ID'
COL_TIME = '会话开始时间'
COL_QUESTION = '用户问题'
COL_ANSWER = '回答答案'
COL_AGENT = 'Agent工作状态'
COL_RAG = 'Rag工作状态'
COL_DOC = 'Doc工作状态'
COL_USER_NAME = '用户姓名'
COL_USER_ID = '用户ID'
COL_MANUAL = '拉起人工'

STATUS_RULES = {
    COL_AGENT: (['Agent执行异常', 'NO_SKILL_MATCHED', '正常'], '未进行技能检索'),
    COL_RAG: (['正常', '未检索到相关信息'], '未进行知识库检索'),
    COL_DOC: (['Agent执行异常', 'NO_DOC_MATCHED', '正常'], '未进行文档检索'),
}

OUTPUT_COLS = [COL_USER_ID, COL_USER_NAME, COL_SESSION, COL_TIME, COL_QUESTION,
               COL_ANSWER, COL_MANUAL, COL_AGENT, COL_RAG, COL_DOC, '合并记录数']


def read_table(path, sheet):
    if path.lower().endswith('.csv'):
        return pd.read_csv(path, dtype=str)
    return pd.read_excel(path, sheet_name=sheet, dtype=str)


def non_empty(series):
    for v in series:
        if pd.notna(v) and str(v).strip():
            return str(v).strip()
    return ''


def merge_status(values, keywords, default):
    text = ' '.join(str(v) for v in values if pd.notna(v))
    for kw in keywords:
        if kw in text:
            return kw
    return default


def merge_group(g):
    g = g.sort_values('_parsed_time', kind='stable')
    row = {
        COL_USER_ID: non_empty(g[COL_USER_ID]),
        COL_USER_NAME: non_empty(g[COL_USER_NAME]),
        COL_SESSION: non_empty(g[COL_SESSION]),
        COL_TIME: '',
        COL_QUESTION: non_empty(g[COL_QUESTION]),
        COL_ANSWER: '\n\n'.join(dict.fromkeys(
            str(v).strip() for v in g[COL_ANSWER] if pd.notna(v) and str(v).strip())),
        COL_MANUAL: '是' if (g[COL_MANUAL].astype(str).str.strip() == '是').any() else '否',
        '合并记录数': len(g),
    }
    t = g['_parsed_time'].dropna()
    if len(t):
        row[COL_TIME] = t.iloc[0].strftime('%Y-%m-%d %H:%M:%S')
    else:
        row[COL_TIME] = non_empty(g[COL_TIME])
    for col, (keywords, default) in STATUS_RULES.items():
        row[col] = merge_status(g[col], keywords, default)
    return row


def main():
    parser = argparse.ArgumentParser(description='按 用户ID+会话ID 合并咨询记录')
    parser.add_argument('--input', required=True, help='原始咨询记录Excel/CSV')
    parser.add_argument('--output', default='会话合并结果.xlsx', help='输出Excel路径')
    parser.add_argument('--sheet', default=0, help='Excel的sheet名或索引，默认第一个sheet')
    args = parser.parse_args()

    df = read_table(args.input, args.sheet)
    missing_cols = [c for c in [COL_SESSION, COL_TIME, COL_QUESTION, COL_ANSWER, COL_AGENT,
                                COL_RAG, COL_DOC, COL_USER_NAME, COL_USER_ID, COL_MANUAL]
                    if c not in df.columns]
    if missing_cols:
        print(f'缺少字段：{missing_cols}；现有字段：{list(df.columns)}')
        return 1

    df['_parsed_time'] = pd.to_datetime(
        df[COL_TIME].astype(str).str.replace('：', ':', regex=False), errors='coerce')

    has_key = df[COL_SESSION].notna() & (df[COL_SESSION].astype(str).str.strip() != '') \
        & df[COL_USER_ID].notna() & (df[COL_USER_ID].astype(str).str.strip() != '')
    df['_gid'] = ''
    df.loc[has_key, '_gid'] = (df.loc[has_key, COL_USER_ID].astype(str).str.strip()
                               + '||' + df.loc[has_key, COL_SESSION].astype(str).str.strip())
    singles = (~has_key).sum()
    df.loc[~has_key, '_gid'] = ['__单行_%d' % i for i in range(singles)]

    merged = pd.DataFrame([merge_group(g) for _, g in df.groupby('_gid', sort=False)])
    merged = merged[OUTPUT_COLS].sort_values([COL_USER_ID, COL_TIME], kind='stable')

    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        merged.to_excel(writer, sheet_name='会话合并结果', index=False)

    manual_yes = (merged[COL_MANUAL] == '是').sum()
    print(f'输入记录：{len(df)}行')
    print(f'合并后会话：{len(merged)}个（其中拉起人工=是：{manual_yes}个，拉起人工=否：{len(merged) - manual_yes}个）')
    if singles:
        print(f'会话ID或用户ID缺失、无法合并单独成行的记录：{singles}行')
    multi = (merged['合并记录数'] > 1).sum()
    print(f'由多行合并而成的会话：{multi}个')
    print(f'\n结果已写入：{args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
