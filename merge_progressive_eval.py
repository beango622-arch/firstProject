# -*- coding: utf-8 -*-
"""
渐进交付策略评估结果合并脚本。

背景：知识库输出和技能输出是分别评估的，两张表各有一份评估结果。为尽可能还原用户
最终拿到答案的真实情况，把两张表按"评估数据行号"关联，每个行号只保留一行数据。

输入：
    知识库评估结果Excel（第一次输出）
    技能评估结果Excel（技能处理之后的第二次输出）
    使用字段：评估数据行号、输入、耗时（毫秒）、消耗token、评估分数、评估结果、原因

合并规则（同一评估数据行号）：
    - 两张表中只有一个"评估通过"       -> 取评估通过的那一行的全部数据
    - 两个都"评估通过"或都"评估不通过"  -> 取技能表（第二次输出）的那一行
    - 只在一张表中有效（另一张表无该行，或该行因异常被剔除） -> 取该表的那一行

输出（写入一个Excel文件，多个sheet）：
    - 合并结果     ：每个评估数据行号一行，附"答案来源""选择依据"
                     （两次都是完整执行的工作流，耗时、token本身就是完整值，直接取被选中那一行的值）
    - 汇总统计     ：来源分布、有效答案覆盖率（两个答案中至少一个评估通过）、耗时/token/评估分数均值
    - 两表对照明细 ：同一行号在两张表中的评估结果、耗时、token并列，便于核对
    - 异常数据     ：行号缺失、行号重复、评估结果取值不合法的行（已从合并中剔除）

用法：
    python3 merge_progressive_eval.py <知识库评估.xlsx> <技能评估.xlsx>
        [--kb-sheet SHEET] [--skill-sheet SHEET] [--output 输出路径]
"""

import argparse
import json
import sys

import pandas as pd

COL_ID = '评估数据行号'
COL_INPUT = '输入'
COL_COST_MS = '耗时'
COL_SCORE = '评估分数'
COL_RESULT = '评估结果'
COL_REASON = '原因'
TOKEN_COL_CANDIDATES = ['消耗token', '消耗Token', 'Token消耗', 'token消耗']
COL_TOKEN = '消耗token'

RESULT_PASS = '评估通过'
RESULT_FAIL = '评估不通过'
VALID_RESULTS = {RESULT_PASS, RESULT_FAIL}

SOURCE_KB = '知识库'
SOURCE_SKILL = '技能'

DATA_COLS = [COL_ID, COL_INPUT, COL_COST_MS, COL_TOKEN, COL_SCORE, COL_RESULT, COL_REASON]


def normalize_id(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith('.0') and text[:-2].lstrip('-').isdigit():
        text = text[:-2]
    return text or None


def extract_question(raw_input):
    if pd.isna(raw_input):
        return None
    try:
        data = json.loads(raw_input)
    except (TypeError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and data.get('question') is not None:
        return str(data['question']).strip()
    return None


def load_table(path, sheet, label):
    df = pd.read_excel(path, sheet_name=sheet)

    token_col = next((c for c in TOKEN_COL_CANDIDATES if c in df.columns), None)
    if token_col is None:
        raise ValueError(f'{label}缺少token字段（可接受的列名：{TOKEN_COL_CANDIDATES}）；现有字段：{list(df.columns)}')
    if token_col != COL_TOKEN:
        df = df.rename(columns={token_col: COL_TOKEN})

    missing = [c for c in DATA_COLS if c not in df.columns]
    if missing:
        raise ValueError(f'{label}缺少字段：{missing}；现有字段：{list(df.columns)}')

    df = df[DATA_COLS].copy()
    df['_id'] = df[COL_ID].apply(normalize_id)
    df[COL_RESULT] = df[COL_RESULT].apply(lambda v: str(v).strip() if pd.notna(v) else v)
    return df


def split_valid(df, label):
    """剔除行号缺失、行号重复、评估结果不合法的行，返回(有效行, 异常行)。"""
    df = df.copy()
    reasons = pd.Series('', index=df.index)

    reasons[df['_id'].isna()] = '评估数据行号缺失'
    dup_mask = df['_id'].notna() & df.duplicated('_id', keep=False)
    reasons[dup_mask] = '评估数据行号在同一张表内重复'
    bad_result = ~df[COL_RESULT].isin(VALID_RESULTS)
    reasons[bad_result & (reasons == '')] = f'评估结果不是"{RESULT_PASS}"或"{RESULT_FAIL}"'

    anomaly = df[reasons != ''].copy()
    anomaly['_异常原因'] = reasons[reasons != '']
    anomaly['_来源表'] = label
    valid = df[reasons == ''].copy()
    return valid, anomaly


def pick_row(kb_row, skill_row, kb_bad=False, skill_bad=False):
    """返回 (被选中的行, 答案来源, 选择依据)。kb_bad/skill_bad表示该行号在对应表中因异常被剔除。"""
    if kb_row is None:
        note = '知识库表该行异常已剔除' if kb_bad else '知识库表无该行'
        return skill_row, SOURCE_SKILL, f'仅技能表有效（{note}）'
    if skill_row is None:
        note = '技能表该行异常已剔除' if skill_bad else '技能表无该行'
        return kb_row, SOURCE_KB, f'仅知识库表有效（{note}）'

    kb_pass = kb_row[COL_RESULT] == RESULT_PASS
    skill_pass = skill_row[COL_RESULT] == RESULT_PASS
    if kb_pass and not skill_pass:
        return kb_row, SOURCE_KB, '仅知识库评估通过，取知识库'
    if skill_pass and not kb_pass:
        return skill_row, SOURCE_SKILL, '仅技能评估通过，取技能'
    if kb_pass and skill_pass:
        return skill_row, SOURCE_SKILL, '两者均评估通过，取技能'
    return skill_row, SOURCE_SKILL, '两者均评估不通过，取技能'


def merge(kb_valid, skill_valid, kb_bad_ids=frozenset(), skill_bad_ids=frozenset()):
    kb_map = {r['_id']: r for _, r in kb_valid.iterrows()}
    skill_map = {r['_id']: r for _, r in skill_valid.iterrows()}

    all_ids = list(dict.fromkeys(list(skill_map.keys()) + list(kb_map.keys())))
    merged_rows, compare_rows = [], []

    for _id in all_ids:
        kb_row, skill_row = kb_map.get(_id), skill_map.get(_id)
        chosen, source, basis = pick_row(kb_row, skill_row, _id in kb_bad_ids, _id in skill_bad_ids)

        record = {col: chosen[col] for col in DATA_COLS}
        record['问题'] = extract_question(chosen[COL_INPUT])
        record['答案来源'] = source
        record['选择依据'] = basis
        merged_rows.append(record)

        compare_rows.append({
            COL_ID: chosen[COL_ID],
            '问题': record['问题'],
            '知识库_评估结果': kb_row[COL_RESULT] if kb_row is not None else None,
            '知识库_评估分数': kb_row[COL_SCORE] if kb_row is not None else None,
            '知识库_耗时': kb_row[COL_COST_MS] if kb_row is not None else None,
            '知识库_消耗token': kb_row[COL_TOKEN] if kb_row is not None else None,
            '技能_评估结果': skill_row[COL_RESULT] if skill_row is not None else None,
            '技能_评估分数': skill_row[COL_SCORE] if skill_row is not None else None,
            '技能_耗时': skill_row[COL_COST_MS] if skill_row is not None else None,
            '技能_消耗token': skill_row[COL_TOKEN] if skill_row is not None else None,
            '答案来源': source,
            '选择依据': basis,
        })

    merged = pd.DataFrame(merged_rows)
    merged = merged[[COL_ID, '问题', COL_INPUT, COL_COST_MS, COL_TOKEN, COL_SCORE, COL_RESULT, COL_REASON,
                     '答案来源', '选择依据']]
    return merged, pd.DataFrame(compare_rows)


def build_summary(merged):
    total = len(merged)
    rows = [('合并后总行数', total)]
    for source in (SOURCE_KB, SOURCE_SKILL):
        n = int((merged['答案来源'] == source).sum())
        rows.append((f'答案来源={source}', n))
        rows.append((f'答案来源={source}占比', n / total if total else float('nan')))

    covered = int((merged[COL_RESULT] == RESULT_PASS).sum())
    rows.append(('有效答案覆盖数（两个答案中至少一个评估通过）', covered))
    rows.append(('有效答案覆盖率', covered / total if total else float('nan')))

    for col in (COL_COST_MS, COL_TOKEN, COL_SCORE):
        rows.append((f'{col}均值', pd.to_numeric(merged[col], errors='coerce').mean()))

    for basis, n in merged['选择依据'].value_counts().items():
        rows.append((f'选择依据：{basis}', int(n)))
    return pd.DataFrame(rows, columns=['指标', '数值'])


def main():
    parser = argparse.ArgumentParser(description='渐进交付策略评估结果合并脚本')
    parser.add_argument('kb_file', help='知识库评估结果Excel（第一次输出）')
    parser.add_argument('skill_file', help='技能评估结果Excel（第二次输出）')
    parser.add_argument('--kb-sheet', default=0, help='知识库表的sheet名或索引，默认第一个')
    parser.add_argument('--skill-sheet', default=0, help='技能表的sheet名或索引，默认第一个')
    parser.add_argument('--output', default='progressive_eval_merged.xlsx', help='输出Excel路径')
    args = parser.parse_args()

    kb_df = load_table(args.kb_file, args.kb_sheet, '知识库表')
    skill_df = load_table(args.skill_file, args.skill_sheet, '技能表')

    kb_valid, kb_anomaly = split_valid(kb_df, '知识库表')
    skill_valid, skill_anomaly = split_valid(skill_df, '技能表')

    merged, compare = merge(kb_valid, skill_valid,
                            set(kb_anomaly['_id'].dropna()), set(skill_anomaly['_id'].dropna()))
    summary = build_summary(merged)
    anomaly = pd.concat([kb_anomaly, skill_anomaly], ignore_index=True)

    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        merged.to_excel(writer, sheet_name='合并结果', index=False)
        summary.to_excel(writer, sheet_name='汇总统计', index=False)
        compare.to_excel(writer, sheet_name='两表对照明细', index=False)
        anomaly.to_excel(writer, sheet_name='异常数据', index=False)

    print(f'知识库表有效行数：{len(kb_valid)}，技能表有效行数：{len(skill_valid)}')
    print(f'异常行数（已剔除，详见"异常数据"sheet）：知识库表{len(kb_anomaly)}，技能表{len(skill_anomaly)}')
    print(f'合并后总行数：{len(merged)}')
    print()
    print(summary.to_string(index=False))
    print(f'\n结果已写入：{args.output}')


if __name__ == '__main__':
    sys.exit(main())
