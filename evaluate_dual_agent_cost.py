# -*- coding: utf-8 -*-
"""
方向二评测数据清洗脚本：双Agent vs 单Agent 成本侧配对差值计算。

输入：两份跑批结果Excel（双Agent工作流 / 单Agent基线工作流），每行一条测试问题，
      关键字段：
          输入        ：JSON字符串，包含question等字段，用question作为两份文件的关联键
          耗时        ：本次调用总耗时
          Token消耗   ：本次调用总token消耗
      本脚本只比较"耗时""Token消耗"这两个总量字段，不分析节点级别耗时/token拆分。

输出（写入一个Excel文件，多个sheet）：
    - 配对明细     ：按question关联后，逐条列出双Agent/单Agent各项成本指标及差值
    - 汇总统计     ：每个成本指标的均值/中位数/P90差值，以及更稳健的"总量比值"增幅
                     （总量比值 = 双Agent总量之和 / 单Agent总量之和，不受个别样本分母过小
                       导致的离群百分比影响，比"逐行百分比取平均"更可靠，优先参考这一列）
    - 未匹配_双Agent：只在双Agent文件里出现、单Agent文件里找不到对应question的行
    - 未匹配_单Agent：只在单Agent文件里出现、双Agent文件里找不到对应question的行
    - 解析异常     ：输入列JSON解析失败、或缺少question字段的行

用法：
    python3 evaluate_dual_agent_cost.py <双Agent结果.xlsx> <单Agent结果.xlsx> [--output 输出路径]
"""

import argparse
import json
import sys

import pandas as pd

COL_INPUT = '输入'
TARGET_METRICS = ['耗时', 'Token消耗']


def extract_question(raw_input):
    """从'输入'列的JSON字符串里解析出question字段，解析失败返回None。"""
    if pd.isna(raw_input):
        return None
    try:
        data = json.loads(raw_input)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    q = data.get('question')
    if q is None or str(q).strip() == '':
        return None
    return str(q).strip()


def load_and_tag(path, label):
    df = pd.read_excel(path)
    if COL_INPUT not in df.columns:
        raise ValueError(f'{path} 缺少"{COL_INPUT}"列，现有字段：{list(df.columns)}')

    missing_metrics = [c for c in TARGET_METRICS if c not in df.columns]
    if missing_metrics:
        raise ValueError(f'{path} 缺少字段：{missing_metrics}；现有字段：{list(df.columns)}')

    df = df.copy()
    df['_question'] = df[COL_INPUT].apply(extract_question)

    parse_fail = df[df['_question'].isna()].copy()
    parse_fail['_异常原因'] = '输入JSON解析失败或缺少question字段'
    parse_fail['_来源文件'] = label

    ok = df[df['_question'].notna()].copy()

    dup = ok[ok.duplicated('_question', keep=False)]
    if len(dup):
        dup = dup.copy()
        dup['_异常原因'] = 'question在同一文件内重复出现'
        dup['_来源文件'] = label
        parse_fail = pd.concat([parse_fail, dup], ignore_index=True)
        ok = ok.drop_duplicates('_question', keep=False)

    return ok, parse_fail


def build_comparison(dual_df, single_df):
    dual_keep = dual_df[['_question'] + TARGET_METRICS].add_suffix('_双Agent')
    dual_keep = dual_keep.rename(columns={'_question_双Agent': '_question'})
    single_keep = single_df[['_question'] + TARGET_METRICS].add_suffix('_单Agent')
    single_keep = single_keep.rename(columns={'_question_单Agent': '_question'})

    merged = dual_keep.merge(single_keep, on='_question', how='inner')
    merged = merged.rename(columns={'_question': '问题'})

    for col in TARGET_METRICS:
        a = merged[f'{col}_双Agent']
        b = merged[f'{col}_单Agent']
        merged[f'{col}_差值(双-单)'] = a - b

    # 按"问题、每个指标的双/单/差值"的顺序重排列，便于阅读
    ordered_cols = ['问题']
    for col in TARGET_METRICS:
        ordered_cols += [f'{col}_双Agent', f'{col}_单Agent', f'{col}_差值(双-单)']
    merged = merged[ordered_cols]

    return merged


def build_summary(detail_df):
    rows = []
    n = len(detail_df)
    for col in TARGET_METRICS:
        dual_vals = detail_df[f'{col}_双Agent']
        single_vals = detail_df[f'{col}_单Agent']
        diff = detail_df[f'{col}_差值(双-单)']

        dual_sum = dual_vals.sum()
        single_sum = single_vals.sum()
        ratio = (dual_sum / single_sum) if single_sum else float('nan')
        ratio_pct = (ratio - 1) * 100 if pd.notna(ratio) else float('nan')

        rows.append({
            '指标': col,
            '样本数': n,
            '双Agent均值': dual_vals.mean(),
            '单Agent均值': single_vals.mean(),
            '差值均值': diff.mean(),
            '差值中位数': diff.median(),
            '差值P90': diff.quantile(0.9),
            '双Agent总量': dual_sum,
            '单Agent总量': single_sum,
            '总量比值(双/单)': ratio,
            '总量比值增幅%': ratio_pct,
        })
    return pd.DataFrame(rows)


def find_unmatched(df, other_df, label):
    unmatched = df[~df['_question'].isin(other_df['_question'])].copy()
    unmatched['_来源文件'] = label
    return unmatched


def main():
    parser = argparse.ArgumentParser(description='双Agent vs 单Agent 成本侧配对差值计算脚本')
    parser.add_argument('dual_agent_file', help='双Agent工作流跑批结果Excel路径')
    parser.add_argument('single_agent_file', help='单Agent基线工作流跑批结果Excel路径')
    parser.add_argument('--output', default='dual_agent_cost_comparison.xlsx', help='输出Excel文件路径')
    args = parser.parse_args()

    dual_df, dual_parse_fail = load_and_tag(args.dual_agent_file, '双Agent')
    single_df, single_parse_fail = load_and_tag(args.single_agent_file, '单Agent')

    detail = build_comparison(dual_df, single_df)
    summary = build_summary(detail)

    unmatched_dual = find_unmatched(dual_df, single_df, '双Agent')
    unmatched_single = find_unmatched(single_df, dual_df, '单Agent')
    parse_fail_all = pd.concat([dual_parse_fail, single_parse_fail], ignore_index=True)

    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        detail.to_excel(writer, sheet_name='配对明细', index=False)
        summary.to_excel(writer, sheet_name='汇总统计', index=False)
        unmatched_dual.to_excel(writer, sheet_name='未匹配_双Agent', index=False)
        unmatched_single.to_excel(writer, sheet_name='未匹配_单Agent', index=False)
        parse_fail_all.to_excel(writer, sheet_name='解析异常', index=False)

    print(f'双Agent文件有效行数：{len(dual_df)}，单Agent文件有效行数：{len(single_df)}')
    print(f'成功配对的问题数：{len(detail)}')
    print(f'仅双Agent文件存在（未匹配）：{len(unmatched_dual)}')
    print(f'仅单Agent文件存在（未匹配）：{len(unmatched_single)}')
    print(f'解析异常行数：{len(parse_fail_all)}')
    print(f'参与比较的指标列：{TARGET_METRICS}')
    print()
    print('汇总统计：')
    print(summary.to_string(index=False))
    print(f'\n结果已写入：{args.output}')


if __name__ == '__main__':
    sys.exit(main())
