# -*- coding: utf-8 -*-
"""
方向一评测数据清洗脚本：候选技能送达率统计 + KB/技能答案配对比较。

输入：会话列表Excel（同一会话ID可能对应最多3行：KB行/Agent行/Doc行，
      行类型由字段取值模式判定，无需依赖行顺序或时间戳）。

输出（写入一个Excel文件，多个sheet）：
    - 异常会话               ：结构不符合预期、已从统计中剔除的会话明细
    - 表1_候选技能送达率_明细 ：候选技能存在的会话逐条明细（含送达结果）
    - 表1_候选技能送达率_统计 ：整体 + 按KB检索结果拆分的送达率统计
    - 表2_KB与技能答案配对    ：KB有答案且技能成功送达的会话，KB答案与技能答案并列

用法：
    python3 evaluate_delivery_rate.py <输入Excel路径> [--sheet SHEET_NAME] [--output 输出路径]
"""

import argparse
import sys

import pandas as pd

# ------------------------- 字段与状态值常量 -------------------------

COL_SESSION_ID = '会话ID'
COL_SESSION_START = '会话开始时间'
COL_QUESTION = '用户问题'
COL_ANSWER = '回答答案'
COL_AGENT_STATUS = 'Agent工作状态'
COL_RAG_STATUS = 'Rag工作状态'
COL_DOC_STATUS = 'Doc工作状态'

REQUIRED_COLUMNS = [
    COL_SESSION_ID, COL_SESSION_START, COL_QUESTION, COL_ANSWER,
    COL_AGENT_STATUS, COL_RAG_STATUS, COL_DOC_STATUS,
]

# KB行：Rag工作状态为这两个值之一（该行Agent/Doc字段固定为占位值，不作为判定依据）
RAG_STATUS_HIT = '正常'
RAG_STATUS_MISS = '未检索到相关信息'
KB_ROW_RAG_VALUES = {RAG_STATUS_HIT, RAG_STATUS_MISS}

# Agent行（技能执行环节）：Agent工作状态为这三个值之一
AGENT_STATUS_OK = '正常'
AGENT_STATUS_EXEC_ERROR = 'Agent执行异常'
AGENT_STATUS_NO_SKILL = 'NO_SKILL_MATCHED'
AGENT_ROW_STATUS_VALUES = {AGENT_STATUS_OK, AGENT_STATUS_EXEC_ERROR, AGENT_STATUS_NO_SKILL}

# KB行里Agent字段的占位值（代表"还未进行技能检索"，不代表Agent行本身）
AGENT_STATUS_NOT_STARTED = '未进行技能检索'

# Doc行：Doc工作状态为这三个值之一（本次评测不分析Doc环节，仅用于行分类与完整性校验）
DOC_STATUS_OK = '正常'
DOC_STATUS_EXEC_ERROR = 'Agent执行异常'
DOC_STATUS_NO_DOC = 'NO_DOC_MATCHED'
DOC_ROW_STATUS_VALUES = {DOC_STATUS_OK, DOC_STATUS_EXEC_ERROR, DOC_STATUS_NO_DOC}

BLANK_VALUES = {'空白', '', None}


def _is_blank(value):
    if pd.isna(value):
        return True
    return str(value).strip() in BLANK_VALUES


def classify_row(row):
    """返回该行的类型：'kb' / 'agent' / 'doc' / 'unclassified'。"""
    rag = row[COL_RAG_STATUS]
    agent = row[COL_AGENT_STATUS]
    doc = row[COL_DOC_STATUS]

    is_kb = (not _is_blank(rag)) and str(rag).strip() in KB_ROW_RAG_VALUES
    is_agent = (not _is_blank(agent)) and str(agent).strip() in AGENT_ROW_STATUS_VALUES
    is_doc = (not _is_blank(doc)) and str(doc).strip() in DOC_ROW_STATUS_VALUES

    matched = [t for t, ok in (('kb', is_kb), ('agent', is_agent), ('doc', is_doc)) if ok]
    if len(matched) == 1:
        return matched[0]
    # 同一行命中0个或多个类型，均视为无法分类（数据异常）
    return 'unclassified'


def load_sessions(input_path, sheet_name=0):
    df = pd.read_excel(input_path, sheet_name=sheet_name)
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f'输入文件缺少必要字段：{missing_cols}；现有字段：{list(df.columns)}')
    df = df.copy()
    df['_行类型'] = df.apply(classify_row, axis=1)
    return df


def split_valid_and_anomalous(df):
    """
    按会话ID分组校验：
        - KB行应当恰好1行（会话必然先经过知识库检索这一步）
        - Agent行最多1行（可以是0行，代表候选技能不存在）
        - Doc行最多1行
        - 不允许存在unclassified行
    任一条件不满足，整条会话标记为异常，整体移入"异常会话"表，不参与后续任何统计。
    """
    anomaly_rows = []
    valid_session_ids = []

    for session_id, g in df.groupby(COL_SESSION_ID, sort=False):
        counts = g['_行类型'].value_counts()
        n_kb = counts.get('kb', 0)
        n_agent = counts.get('agent', 0)
        n_doc = counts.get('doc', 0)
        n_unclassified = counts.get('unclassified', 0)

        reasons = []
        if n_kb != 1:
            reasons.append(f'KB行数量异常(应为1，实际{n_kb})')
        if n_agent > 1:
            reasons.append(f'Agent行数量异常(应<=1，实际{n_agent})')
        if n_doc > 1:
            reasons.append(f'Doc行数量异常(应<=1，实际{n_doc})')
        if n_unclassified > 0:
            reasons.append(f'存在无法分类的行({n_unclassified}行)')

        if reasons:
            g = g.copy()
            g['异常原因'] = '；'.join(reasons)
            anomaly_rows.append(g)
        else:
            valid_session_ids.append(session_id)

    anomaly_df = (
        pd.concat(anomaly_rows, ignore_index=True)
        if anomaly_rows else
        pd.DataFrame(columns=list(df.columns) + ['异常原因'])
    )
    valid_df = df[df[COL_SESSION_ID].isin(valid_session_ids)].copy()
    return valid_df, anomaly_df


def build_session_level_table(valid_df):
    """把校验通过的明细行，按会话聚合成一行一会话的宽表，方便后续两张表直接筛选。"""
    records = []
    for session_id, g in valid_df.groupby(COL_SESSION_ID, sort=False):
        kb_row = g[g['_行类型'] == 'kb'].iloc[0] if (g['_行类型'] == 'kb').any() else None
        agent_rows = g[g['_行类型'] == 'agent']
        agent_row = agent_rows.iloc[0] if len(agent_rows) else None

        session_start = g[COL_SESSION_START].dropna()
        session_start = session_start.iloc[0] if len(session_start) else None
        question = g[COL_QUESTION].dropna()
        question = question.iloc[0] if len(question) else None

        records.append({
            COL_SESSION_ID: session_id,
            COL_SESSION_START: session_start,
            COL_QUESTION: question,
            'Rag工作状态': kb_row[COL_RAG_STATUS] if kb_row is not None else None,
            'KB回答答案': kb_row[COL_ANSWER] if kb_row is not None else None,
            '候选技能存在': agent_row is not None,
            'Agent工作状态': agent_row[COL_AGENT_STATUS] if agent_row is not None else None,
            '技能回答答案': agent_row[COL_ANSWER] if agent_row is not None else None,
        })
    return pd.DataFrame(records)


def build_table1(session_df):
    """表1：候选技能存在的会话，送达率明细 + 统计（整体 / 按KB检索结果拆分）。"""
    cand = session_df[session_df['候选技能存在']].copy()
    cand['送达成功'] = cand['Agent工作状态'] == AGENT_STATUS_OK
    cand['未送达原因'] = cand['Agent工作状态'].where(~cand['送达成功'], None)

    detail_cols = [
        COL_SESSION_ID, COL_SESSION_START, COL_QUESTION,
        'Rag工作状态', 'Agent工作状态', '送达成功', '未送达原因',
    ]
    detail = cand[detail_cols].reset_index(drop=True)

    def _summarize(group_df, group_name):
        total = len(group_df)
        delivered = int(group_df['送达成功'].sum())
        exec_error = int((group_df['Agent工作状态'] == AGENT_STATUS_EXEC_ERROR).sum())
        no_skill = int((group_df['Agent工作状态'] == AGENT_STATUS_NO_SKILL).sum())
        rate = delivered / total if total else float('nan')
        return {
            '统计口径': group_name,
            '候选技能会话数': total,
            '送达成功数': delivered,
            '送达率': rate,
            'Agent执行异常数': exec_error,
            'NO_SKILL_MATCHED数': no_skill,
        }

    summary_rows = [_summarize(cand, '整体（全部候选技能会话）')]
    for rag_status, group_name in (
        (RAG_STATUS_HIT, 'KB有答案 + 候选技能存在'),
        (RAG_STATUS_MISS, 'KB无答案 + 候选技能存在'),
    ):
        sub = cand[cand['Rag工作状态'] == rag_status]
        summary_rows.append(_summarize(sub, group_name))

    summary = pd.DataFrame(summary_rows)
    return detail, summary


def build_table2(session_df):
    """表2：KB有答案 且 技能成功送达 的会话，KB答案与技能答案并列，供后续质量比较使用。"""
    mask = (session_df['Rag工作状态'] == RAG_STATUS_HIT) & (session_df['Agent工作状态'] == AGENT_STATUS_OK)
    pair_df = session_df[mask][[
        COL_SESSION_ID, COL_SESSION_START, COL_QUESTION, 'KB回答答案', '技能回答答案',
    ]].reset_index(drop=True)
    return pair_df


def main():
    parser = argparse.ArgumentParser(description='候选技能送达率统计 + KB/技能答案配对清洗脚本')
    parser.add_argument('input', help='输入的会话列表Excel文件路径')
    parser.add_argument('--sheet', default=0, help='输入文件的sheet名或索引，默认取第一个sheet')
    parser.add_argument('--output', default='delivery_rate_evaluation.xlsx', help='输出Excel文件路径')
    args = parser.parse_args()

    df = load_sessions(args.input, sheet_name=args.sheet)
    valid_df, anomaly_df = split_valid_and_anomalous(df)
    session_df = build_session_level_table(valid_df)

    table1_detail, table1_summary = build_table1(session_df)
    table2_pair = build_table2(session_df)

    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        anomaly_df.to_excel(writer, sheet_name='异常会话', index=False)
        table1_detail.to_excel(writer, sheet_name='表1_送达率_明细', index=False)
        table1_summary.to_excel(writer, sheet_name='表1_送达率_统计', index=False)
        table2_pair.to_excel(writer, sheet_name='表2_KB与技能答案配对', index=False)

    n_total_sessions = df[COL_SESSION_ID].nunique()
    n_valid_sessions = len(session_df)
    n_anomaly_sessions = anomaly_df[COL_SESSION_ID].nunique() if len(anomaly_df) else 0

    print(f'原始会话数：{n_total_sessions}')
    print(f'异常会话数（已剔除，详见"异常会话"sheet）：{n_anomaly_sessions}')
    print(f'有效会话数（参与统计）：{n_valid_sessions}')
    print(f'候选技能存在的会话数：{len(table1_detail)}')
    print(f'KB有答案且技能成功送达的会话数（表2）：{len(table2_pair)}')
    print()
    print('表1统计结果：')
    print(table1_summary.to_string(index=False))
    print(f'\n结果已写入：{args.output}')


if __name__ == '__main__':
    sys.exit(main())
