# -*- coding: utf-8 -*-
"""
方向二评测数据清洗脚本：双Agent vs 单Agent 成本侧配对差值计算。

输入：两份跑批结果Excel（双Agent工作流 / 单Agent基线工作流），每行一条测试问题，
      关键字段：
          输入        ：JSON字符串，包含question等字段，用question作为两份文件的关联键
          耗时        ：本次调用总耗时
          Token消耗   ：本次调用总token消耗
          （以及可能存在的、按节点拆分的其它"XX耗时"/"XXToken消耗"列）
          节点Id（开始）/节点名称（开始）等 ：节点标识信息，不参与指标计算

输出（写入一个Excel文件，多个sheet）：
    - 配对明细     ：按question关联后，逐条列出双Agent/单Agent各项成本指标及差值
    - 汇总统计     ：每个成本指标的均值/中位数/P90差值、平均增幅百分比
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


def is_metric_column(col_name):
    """判定一列是否是需要参与配对差值计算的成本指标列（耗时/Token消耗类），
    排除节点Id/节点名称等标识类列。"""
    name = str(col_name)
    if 'id' in name.lower() or '名称' in name:
        return False
    return ('耗时' in name) or ('token' in name.lower())


def load_and_tag(path, label):
    df = pd.read_excel(path)
    if COL_INPUT not in df.columns:
        raise ValueError(f'{path} 缺少"{COL_INPUT}"列，现有字段：{list(df.columns)}')

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

    metric_cols = [c for c in ok.columns if is_metric_column(c)]
    if not metric_cols:
        raise ValueError(f'{path} 没有识别到任何"耗时"/"Token消耗"相关的指标列，请检查列名')

    return ok, parse_fail, metric_cols


def build_comparison(dual_df, dual_metrics, single_df, single_metrics):
    common_metrics = [c for c in dual_metrics if c in single_metrics]
    if not common_metrics:
        raise ValueError(
            f'两份文件没有同名的成本指标列可比较。\n'
            f'双Agent文件指标列：{dual_metrics}\n'
            f'单Agent文件指标列：{single_metrics}'
        )

    dual_keep = dual_df[['_question'] + common_metrics].add_suffix('_双Agent')
    dual_keep = dual_keep.rename(columns={'_question_双Agent': '_question'})
    single_keep = single_df[['_question'] + common_metrics].add_suffix('_单Agent')
    single_keep = single_keep.rename(columns={'_question_单Agent': '_question'})

    merged = dual_keep.merge(single_keep, on='_question', how='inner')
    merged = merged.rename(columns={'_question': '问题'})

    for col in common_metrics:
        a = merged[f'{col}_双Agent']
        b = merged[f'{col}_单Agent']
        merged[f'{col}_差值(双-单)'] = a - b
        merged[f'{col}_增幅%'] = (a - b) / b.replace(0, pd.NA) * 100

    # 按"问题、每个指标的双/单/差值/增幅%"的顺序重排列，便于阅读
    ordered_cols = ['问题']
    for col in common_metrics:
        ordered_cols += [f'{col}_双Agent', f'{col}_单Agent', f'{col}_差值(双-单)', f'{col}_增幅%']
    merged = merged[ordered_cols]

    return merged, common_metrics


def build_summary(detail_df, common_metrics):
    rows = []
    n = len(detail_df)
    for col in common_metrics:
        diff = detail_df[f'{col}_差值(双-单)']
        pct = detail_df[f'{col}_增幅%']
        rows.append({
            '指标': col,
            '样本数': n,
            '双Agent均值': detail_df[f'{col}_双Agent'].mean(),
            '单Agent均值': detail_df[f'{col}_单Agent'].mean(),
            '差值均值': diff.mean(),
            '差值中位数': diff.median(),
            '差值P90': diff.quantile(0.9),
            '平均增幅%': pct.mean(),
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

    dual_df, dual_parse_fail, dual_metrics = load_and_tag(args.dual_agent_file, '双Agent')
    single_df, single_parse_fail, single_metrics = load_and_tag(args.single_agent_file, '单Agent')

    detail, common_metrics = build_comparison(dual_df, dual_metrics, single_df, single_metrics)
    summary = build_summary(detail, common_metrics)

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
    print(f'参与比较的指标列：{common_metrics}')
    print()
    print('汇总统计：')
    print(summary.to_string(index=False))
    print(f'\n结果已写入：{args.output}')


if __name__ == '__main__':
    sys.exit(main())
