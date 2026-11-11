# -*- coding: utf-8 -*-
"""
渐进交付 / 知识库优先 / 技能优先 三种策略的评估结果合并与对比脚本。

输入（4张评估结果Excel，表结构一致，每张都是完整执行工作流后的独立评估）：
    --progressive-kb     渐进交付：知识库检索结果的第一次输出
    --progressive-skill  渐进交付：技能处理之后的第二次输出
    --kb-first           知识库优先策略（命中知识库即结束，未命中转技能）
    --skill-first        技能优先策略（命中技能即结束，未命中转知识库）
    后两张可以不传，只传前两张时只做渐进交付的合并。
    使用字段：评估数据行号、输入、耗时（毫秒）、消耗token、评估分数、评估结果、原因

第一步：渐进交付两张表合并（同一评估数据行号只保留一行）
    - 两张表中只有一个"评估通过"       -> 取评估通过的那一行的全部数据
    - 两个都"评估通过"或都"评估不通过"  -> 取技能表（第二次输出）的那一行
    - 只在一张表中有效（另一张表无该行，或该行因异常被剔除） -> 取该表的那一行
    两次都是完整执行的工作流，耗时、token本身就是完整值，直接取被选中那一行的值。
    渐进交付用户最终能看到两个答案，所以它的指标是"有效答案覆盖率"：两个答案中至少有一个评估通过。

第二步：三种策略对比（只统计三张/四张表都有效的评估数据行号，保证是同一批问题）
    - 有效答案覆盖率：评估通过的题数占比（知识库优先、技能优先各只有一个答案，按该答案计算）
    - 平均评估分数、平均耗时、平均token、总token、总耗时
    - 每个有效答案的成本：总token（总耗时）除以评估通过的题数
    - 逐题配对：两两对比"都通过/仅A通过/仅B通过/都不通过"的题数

第三步：无候选技能问题的节约token（验证"减少无谓推理"，需要同时传入--skill-first）
    - 渐进交付工作流在没有候选技能时，答案里会带固定标识（默认NO_SKILL_MATCHED），
      脚本据此标记"无候选技能"的问题。答案列自动识别，也可用--answer-col指定。
    - 节约token = 这部分问题在技能优先中的token - 在渐进交付中的token。
    - 传入--daily-filtered（每日被提问有效性过滤的问题数）时，另估算每日节约token
      = 每日过滤数 × 渐进交付单题平均token。

输出（写入一个Excel文件，多个sheet）：
    - 三策略对比       ：三种策略的汇总指标
    - 配对对比         ：两两逐题配对的题数
    - 逐题对比明细     ：每个评估数据行号在三种策略下的评估结果、分数、耗时、token
    - 无候选技能节约_汇总 / _明细 ：无候选技能问题的节约token（传了--skill-first且识别到答案列时生成）
    - 渐进交付合并结果 ：每个行号一行，附"答案来源""选择依据"
    - 渐进交付汇总     ：渐进交付的来源分布、选择依据分布
    - 两表对照明细     ：渐进交付两张表同一行号的数据并列，便于核对
    - 异常数据         ：行号缺失、行号重复、评估结果取值不合法的行（已从统计中剔除）

用法：
    python3 evaluate_strategies.py --progressive-kb 渐进_第一次输出.xlsx \
        --progressive-skill 渐进_第二次输出.xlsx --kb-first 知识库优先.xlsx \
        --skill-first 技能优先.xlsx [--answer-col 答案列名] [--no-skill-tag 标识]
        [--daily-filtered 每日过滤数] [--sheet SHEET] [--output 输出路径]
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
ANSWER_COL_CANDIDATES = ['最终答案', '输出', '输出结果', '回答答案', '回答', '答案', '实际输出', 'output', 'answer']
DEFAULT_NO_SKILL_TAG = 'NO_SKILL_MATCHED'

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


def load_table(path, sheet, label, answer_col=None):
    df = pd.read_excel(path, sheet_name=sheet)

    token_col = next((c for c in TOKEN_COL_CANDIDATES if c in df.columns), None)
    if token_col is None:
        raise ValueError(f'{label}缺少token字段（可接受的列名：{TOKEN_COL_CANDIDATES}）；现有字段：{list(df.columns)}')
    if token_col != COL_TOKEN:
        df = df.rename(columns={token_col: COL_TOKEN})

    missing = [c for c in DATA_COLS if c not in df.columns]
    if missing:
        raise ValueError(f'{label}缺少字段：{missing}；现有字段：{list(df.columns)}')

    found_answer_col = answer_col if answer_col in df.columns else next(
        (c for c in ANSWER_COL_CANDIDATES if c in df.columns), None)
    keep = DATA_COLS + ([found_answer_col] if found_answer_col else [])
    df = df[keep].copy()
    if found_answer_col:
        df = df.rename(columns={found_answer_col: '_答案'})
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


def find_no_skill_ids(tables, tag):
    """tables: 渐进交付的有效行DataFrame列表。答案里包含固定标识的行号，视为"无候选技能"。"""
    ids, has_answer_col = set(), False
    for df in tables:
        if '_答案' not in df.columns:
            continue
        has_answer_col = True
        mask = df['_答案'].apply(lambda v: tag.upper() in str(v).upper() if pd.notna(v) else False)
        ids |= set(df.loc[mask, '_id'])
    return ids, has_answer_col


def build_no_skill_saving(strategies, common_ids, no_skill_ids, daily_filtered):
    """无候选技能的问题：技能优先消耗 - 渐进交付消耗 = 节约。返回(汇总表, 明细表)。"""
    ids = [i for i in common_ids if i in no_skill_ids]
    prog, skill_first = strategies['渐进交付'], strategies['技能优先']

    def num(row, col):
        return pd.to_numeric(row[col], errors='coerce')

    detail_rows = []
    for i in ids:
        pr, sr = prog[i], skill_first[i]
        detail_rows.append({
            COL_ID: pr[COL_ID],
            '问题': extract_question(pr[COL_INPUT]),
            '技能优先_消耗token': num(sr, COL_TOKEN),
            '渐进交付_消耗token': num(pr, COL_TOKEN),
            '节约token(技能优先-渐进交付)': num(sr, COL_TOKEN) - num(pr, COL_TOKEN),
            '技能优先_耗时(毫秒)': num(sr, COL_COST_MS),
            '渐进交付_耗时(毫秒)': num(pr, COL_COST_MS),
            '节约耗时(毫秒)': num(sr, COL_COST_MS) - num(pr, COL_COST_MS),
        })
    detail = pd.DataFrame(detail_rows)

    n = len(ids)
    rows = [
        ('参与对比的题数（三策略共有）', len(common_ids)),
        ('渐进交付判定为无候选技能的题数', n),
        ('占比', n / len(common_ids) if common_ids else float('nan')),
    ]
    if n:
        sf_sum, pg_sum = detail['技能优先_消耗token'].sum(), detail['渐进交付_消耗token'].sum()
        rows += [
            ('这部分题在技能优先中的平均token', detail['技能优先_消耗token'].mean()),
            ('这部分题在渐进交付中的平均token', detail['渐进交付_消耗token'].mean()),
            ('平均每题节约token', detail['节约token(技能优先-渐进交付)'].mean()),
            ('合计节约token', sf_sum - pg_sum),
            ('节约比例', (sf_sum - pg_sum) / sf_sum if sf_sum else float('nan')),
            ('平均每题节约耗时(毫秒)', detail['节约耗时(毫秒)'].mean()),
        ]
    if daily_filtered is not None:
        avg_token = pd.to_numeric(pd.Series([r[COL_TOKEN] for r in prog.values()]), errors='coerce').mean()
        rows += [
            ('每日被过滤的问题数（输入值）', daily_filtered),
            ('渐进交付单题平均token（全部题）', avg_token),
            ('每日过滤节约的token估算（每日过滤数×单题平均token）', daily_filtered * avg_token),
        ]
    return pd.DataFrame(rows, columns=['指标', '数值']), detail


def build_progressive_summary(merged):
    total = len(merged)
    rows = [('合并后总行数', total)]
    for source in (SOURCE_KB, SOURCE_SKILL):
        n = int((merged['答案来源'] == source).sum())
        rows.append((f'答案来源={source}', n))
        rows.append((f'答案来源={source}占比', n / total if total else float('nan')))

    covered = int((merged[COL_RESULT] == RESULT_PASS).sum())
    rows.append(('有效答案覆盖数（两个答案中至少一个评估通过）', covered))
    rows.append(('有效答案覆盖率', covered / total if total else float('nan')))

    for basis, n in merged['选择依据'].value_counts().items():
        rows.append((f'选择依据：{basis}', int(n)))
    return pd.DataFrame(rows, columns=['指标', '数值'])


def strategy_rows(df):
    """把有效行转成 {评估数据行号: 行} 的字典，用于跨策略按行号关联。"""
    return {r['_id']: r for _, r in df.iterrows()}


def build_strategy_comparison(strategies, common_ids):
    """strategies: {策略名: {id: 行}}；只统计common_ids里的行号。返回(汇总表, 逐题明细表)。"""
    summary_rows = []
    for name, rows in strategies.items():
        sub = [rows[i] for i in common_ids]
        n = len(sub)
        passed = sum(1 for r in sub if r[COL_RESULT] == RESULT_PASS)
        scores = pd.to_numeric(pd.Series([r[COL_SCORE] for r in sub]), errors='coerce')
        costs = pd.to_numeric(pd.Series([r[COL_COST_MS] for r in sub]), errors='coerce')
        tokens = pd.to_numeric(pd.Series([r[COL_TOKEN] for r in sub]), errors='coerce')
        total_cost, total_token = costs.sum(), tokens.sum()
        summary_rows.append({
            '策略': name,
            '对比题数': n,
            '有效答案数': passed,
            '有效答案覆盖率': passed / n if n else float('nan'),
            '平均评估分数': scores.mean(),
            '平均耗时(毫秒)': costs.mean(),
            '平均token': tokens.mean(),
            '总耗时(毫秒)': total_cost,
            '总token': total_token,
            '每个有效答案的耗时(毫秒)': total_cost / passed if passed else float('nan'),
            '每个有效答案的token': total_token / passed if passed else float('nan'),
        })

    detail_rows = []
    for i in common_ids:
        first = next(iter(strategies.values()))[i]
        rec = {COL_ID: first[COL_ID], '问题': extract_question(first[COL_INPUT])}
        for name, rows in strategies.items():
            r = rows[i]
            rec[f'{name}_评估结果'] = r[COL_RESULT]
            rec[f'{name}_评估分数'] = r[COL_SCORE]
            rec[f'{name}_耗时'] = r[COL_COST_MS]
            rec[f'{name}_消耗token'] = r[COL_TOKEN]
        detail_rows.append(rec)
    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def build_pairwise(strategies, common_ids):
    names = list(strategies)
    rows = []
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            a, b = names[x], names[y]
            both = only_a = only_b = neither = 0
            for i in common_ids:
                a_pass = strategies[a][i][COL_RESULT] == RESULT_PASS
                b_pass = strategies[b][i][COL_RESULT] == RESULT_PASS
                if a_pass and b_pass:
                    both += 1
                elif a_pass:
                    only_a += 1
                elif b_pass:
                    only_b += 1
                else:
                    neither += 1
            rows.append({
                '策略A': a,
                '策略B': b,
                '对比题数': len(common_ids),
                '两者均通过': both,
                '仅策略A通过': only_a,
                '仅策略B通过': only_b,
                '两者均不通过': neither,
            })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description='三种策略的评估结果合并与对比脚本')
    parser.add_argument('--progressive-kb', required=True, help='渐进交付：知识库第一次输出的评估结果Excel')
    parser.add_argument('--progressive-skill', required=True, help='渐进交付：技能处理后第二次输出的评估结果Excel')
    parser.add_argument('--kb-first', help='知识库优先策略的评估结果Excel（可选）')
    parser.add_argument('--skill-first', help='技能优先策略的评估结果Excel（可选）')
    parser.add_argument('--answer-col', help='答案/输出所在列名，用于识别无候选技能标识；不指定则自动识别常见列名')
    parser.add_argument('--no-skill-tag', default=DEFAULT_NO_SKILL_TAG, help='无候选技能时答案里包含的固定标识')
    parser.add_argument('--daily-filtered', type=float,
                        help='每日被提问有效性过滤的问题数，用于估算每日节约的token（可选）')
    parser.add_argument('--sheet', default=0, help='Excel的sheet名或索引（对所有表生效），默认第一个sheet')
    parser.add_argument('--output', default='strategy_comparison.xlsx', help='输出Excel路径')
    args = parser.parse_args()

    kb_df = load_table(args.progressive_kb, args.sheet, '渐进交付-知识库表', args.answer_col)
    skill_df = load_table(args.progressive_skill, args.sheet, '渐进交付-技能表', args.answer_col)
    kb_valid, kb_anomaly = split_valid(kb_df, '渐进交付-知识库表')
    skill_valid, skill_anomaly = split_valid(skill_df, '渐进交付-技能表')

    merged, compare = merge(kb_valid, skill_valid,
                            set(kb_anomaly['_id'].dropna()), set(skill_anomaly['_id'].dropna()))
    merged_valid = merged.copy()
    merged_valid['_id'] = merged_valid[COL_ID].apply(normalize_id)

    anomalies = [kb_anomaly, skill_anomaly]
    strategies = {'渐进交付': strategy_rows(merged_valid)}
    for label, path in (('知识库优先', args.kb_first), ('技能优先', args.skill_first)):
        if not path:
            continue
        valid, anomaly = split_valid(load_table(path, args.sheet, f'{label}表'), f'{label}表')
        strategies[label] = strategy_rows(valid)
        anomalies.append(anomaly)

    anomaly_all = pd.concat(anomalies, ignore_index=True)
    progressive_summary = build_progressive_summary(merged)

    common_ids = [i for i in strategies['渐进交付'] if all(i in rows for rows in strategies.values())]
    sheets = {}
    if len(strategies) > 1:
        summary, detail = build_strategy_comparison(strategies, common_ids)
        sheets['三策略对比'] = summary
        sheets['配对对比'] = build_pairwise(strategies, common_ids)
        sheets['逐题对比明细'] = detail
    no_skill_ids, has_answer_col = find_no_skill_ids([kb_valid, skill_valid], args.no_skill_tag)
    if '技能优先' in strategies:
        if has_answer_col:
            saving_summary, saving_detail = build_no_skill_saving(
                strategies, common_ids, no_skill_ids, args.daily_filtered)
            sheets['无候选技能节约_汇总'] = saving_summary
            sheets['无候选技能节约_明细'] = saving_detail
        else:
            print('提示：渐进交付两张表里没有找到答案列，无法识别无候选技能的问题；'
                  '请用--answer-col指定答案所在列名。')
    sheets['渐进交付合并结果'] = merged
    sheets['渐进交付汇总'] = progressive_summary
    sheets['两表对照明细'] = compare
    sheets['异常数据'] = anomaly_all

    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)

    print(f'渐进交付：知识库表有效{len(kb_valid)}行，技能表有效{len(skill_valid)}行，合并后{len(merged)}行')
    for name, rows in strategies.items():
        print(f'{name}：有效{len(rows)}行')
    print(f'异常行数（已剔除，详见"异常数据"sheet）：{len(anomaly_all)}')
    if len(strategies) > 1:
        print(f'三种策略共有的评估数据行号（参与对比）：{len(common_ids)}')
        print()
        print(sheets['三策略对比'].to_string(index=False))
        print()
        print(sheets['配对对比'].to_string(index=False))
        if '无候选技能节约_汇总' in sheets:
            print()
            print(sheets['无候选技能节约_汇总'].to_string(index=False))
    else:
        print()
        print(progressive_summary.to_string(index=False))
    print(f'\n结果已写入：{args.output}')


if __name__ == '__main__':
    sys.exit(main())
