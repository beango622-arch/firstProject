# -*- coding: utf-8 -*-
"""生成"3.2 机制成效"配套的论证思路示意图"""
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FONT_PATH = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
cn_font = fm.FontProperties(fname=FONT_PATH)

ASCII_RUN = re.compile(r'[A-Za-z0-9%.+\-/]+')


def tokenize(text):
    tokens, i = [], 0
    while i < len(text):
        m = ASCII_RUN.match(text, i)
        if m:
            tokens.append(m.group())
            i = m.end()
        else:
            tokens.append(text[i])
            i += 1
    return tokens


def token_width(tok):
    return len(tok) * 0.56 if ASCII_RUN.fullmatch(tok) else 1.0


def wrap_cn(text, width):
    if '\n' in text:
        return '\n'.join(wrap_cn(part, width) for part in text.split('\n'))
    lines, cur, cur_w = [], '', 0.0
    for tok in tokenize(text):
        w = token_width(tok)
        if cur_w + w > width and cur:
            lines.append(cur)
            cur, cur_w = '', 0.0
        cur += tok
        cur_w += w
    if cur:
        lines.append(cur)
    return '\n'.join(lines)


def box(ax, cx, cy, w, h, text, facecolor, edgecolor, fontsize=11.5, fontcolor='#222222', bold=False, wrap_width=14.5):
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                        boxstyle='round,pad=0.4,rounding_size=1.2',
                        linewidth=1.6, edgecolor=edgecolor, facecolor=facecolor, zorder=3)
    ax.add_patch(p)
    wrapped = wrap_cn(text, wrap_width)
    ax.text(cx, cy, wrapped, ha='center', va='center', fontproperties=cn_font,
             fontsize=fontsize, color=fontcolor, fontweight='bold' if bold else 'normal',
             linespacing=1.6, zorder=4)
    return (cx, cy, w, h)


def arrow(ax, start, end, color='#666666', lw=1.8, connectionstyle='arc3,rad=0.0', style='-|>'):
    a = FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=16,
                         color=color, linewidth=lw, connectionstyle=connectionstyle, zorder=2)
    ax.add_patch(a)


def label(ax, x, y, text, fontsize=13, color='#444444', bold=True, ha='center', wrap_width=None):
    t = wrap_cn(text, wrap_width) if wrap_width else text
    ax.text(x, y, t, ha=ha, va='center', fontproperties=cn_font,
             fontsize=fontsize, color=color, fontweight='bold' if bold else 'normal', linespacing=1.5)


def main():
    fig, ax = plt.subplots(figsize=(13, 18.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 172)
    ax.invert_yaxis()
    ax.axis('off')

    label(ax, 50, 4, '机制成效的论证思路', fontsize=18, color='#1a1a1a')
    label(ax, 25, 13, '答案是否更有效', fontsize=12.5, color='#1f5fa8')
    label(ax, 75, 13, '资源是否花在需要推理的问题上', fontsize=12.5, color='#b5651d')

    BLUE_F, BLUE_E = '#e8f1fb', '#1f5fa8'
    ORANGE_F, ORANGE_E = '#fdf1e6', '#b5651d'
    AMBER_F, AMBER_E = '#fff4da', '#c9962b'
    GREEN_F, GREEN_E = '#e8f6ee', '#1e8449'

    bw, bh = 40, 16
    yA = [24, 47, 70, 93]
    yB = [24, 47, 70, 93]

    boxA1 = box(ax, 25, yA[0], bw, bh,
                '问题：推理性问题占68.2%，光靠知识库检索答不好', BLUE_F, BLUE_E)
    boxA2 = box(ax, 25, yA[1], bw, bh,
                '方式：知识库、技能推理、文档推荐多源协同', BLUE_F, BLUE_E)
    boxA3 = box(ax, 25, yA[2], bw, bh,
                '评测：与知识库优先、技能优先\n同批120题对比', BLUE_F, BLUE_E)
    boxA4 = box(ax, 25, yA[3], bw, bh,
                '结果：有效答案覆盖率提升', BLUE_F, BLUE_E, bold=True)

    boxB1 = box(ax, 75, yB[0], bw, bh,
                '问题：推理必然带来成本和耗时的上升', ORANGE_F, ORANGE_E)
    boxB2 = box(ax, 75, yB[1], bw, bh,
                '方式：先判断提问是否有效、有无候选技能，再决定是否推理', ORANGE_F, ORANGE_E)
    boxB3 = box(ax, 75, yB[2], bw, bh,
                '评测：无候选技能的问题，对比技能优先的token消耗', ORANGE_F, ORANGE_E)
    boxB4 = box(ax, 75, yB[3], bw, bh,
                '结果：无谓推理消耗降低', ORANGE_F, ORANGE_E, bold=True)

    for x1, x2 in [(boxA1, boxA2), (boxA2, boxA3), (boxA3, boxA4)]:
        arrow(ax, (x1[0], x1[1] + x1[3] / 2), (x2[0], x2[1] - x2[3] / 2))
    for x1, x2 in [(boxB1, boxB2), (boxB2, boxB3), (boxB3, boxB4)]:
        arrow(ax, (x1[0], x1[1] + x1[3] / 2), (x2[0], x2[1] - x2[3] / 2))

    label(ax, 50, 105, '两条线各自成立，一起回答成本是否值得', fontsize=11.5, color='#555555')

    costBox = box(ax, 50, 116, 86, 13,
                   '代价：整体推理消耗高于单一来源策略，要用节约的人力来衡量是否值得',
                   AMBER_F, AMBER_E, fontsize=12.5, bold=True, wrap_width=36)

    arrow(ax, (boxA4[0], boxA4[1] + boxA4[3] / 2), (36, costBox[1] - costBox[3] / 2), connectionstyle='arc3,rad=0.15')
    arrow(ax, (boxB4[0], boxB4[1] + boxB4[3] / 2), (64, costBox[1] - costBox[3] / 2), connectionstyle='arc3,rad=-0.15')

    cBw, cBh, yC = 40, 17, 140
    compC1 = box(ax, 25, yC, cBw, cBh,
                  '新增的有效答案，意味着少一次人工接手，折算为节约的人力', GREEN_F, GREEN_E)
    compC2 = box(ax, 75, yC, cBw, cBh,
                  '无效提问被过滤，不再进入推理\n每日节约的token按估算折算', GREEN_F, GREEN_E)

    arrow(ax, (costBox[0] - 10, costBox[1] + costBox[3] / 2), (compC1[0], compC1[1] - compC1[3] / 2), connectionstyle='arc3,rad=-0.1')
    arrow(ax, (costBox[0] + 10, costBox[1] + costBox[3] / 2), (compC2[0], compC2[1] - compC2[3] / 2), connectionstyle='arc3,rad=0.1')

    concBox = box(ax, 50, 162, 90, 13,
                   '结论：以更高的推理投入，换取更高的有效答案覆盖率和更少的人工处理',
                   GREEN_F, GREEN_E, fontsize=13, bold=True, wrap_width=36)

    arrow(ax, (compC1[0], compC1[1] + compC1[3] / 2), (40, concBox[1] - concBox[3] / 2), connectionstyle='arc3,rad=0.12', color='#1e8449')
    arrow(ax, (compC2[0], compC2[1] + compC2[3] / 2), (60, concBox[1] - concBox[3] / 2), connectionstyle='arc3,rad=-0.12', color='#1e8449')

    plt.tight_layout()
    plt.savefig('logic_chain_diagram.png', dpi=170, bbox_inches='tight', facecolor='white')
    print('saved: logic_chain_diagram.png')


if __name__ == '__main__':
    main()
