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
    fig, ax = plt.subplots(figsize=(13, 13.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 128)
    ax.invert_yaxis()
    ax.axis('off')

    label(ax, 50, 4, '机制成效的论证思路', fontsize=18, color='#1a1a1a')
    label(ax, 25, 12, '评测问题一：能否让更多问题得到有效答案\n（验证价值主张一）', fontsize=12.5, color='#1f5fa8')
    label(ax, 75, 12, '评测问题二：增加多少计算成本，节省多少人力\n（验证价值主张二）', fontsize=12.5, color='#b5651d')

    BLUE_F, BLUE_E = '#e8f1fb', '#1f5fa8'
    ORANGE_F, ORANGE_E = '#fdf1e6', '#b5651d'
    GREEN_F, GREEN_E = '#e8f6ee', '#1e8449'

    bw, bh = 40, 16
    ys = [24, 47, 70, 93]

    boxA = [
        box(ax, 25, ys[0], bw, bh, '问题：推理性问题占68.2%，\n光靠知识库检索答不好', BLUE_F, BLUE_E),
        box(ax, 25, ys[1], bw, bh, '方式：知识库检索、技能推理、文档推荐多源协同', BLUE_F, BLUE_E),
        box(ax, 25, ys[2], bw, bh, '评测：与知识库优先、技能优先\n同批120题对比有效答案覆盖率', BLUE_F, BLUE_E),
        box(ax, 25, ys[3], bw, bh, '结果：新增有效答案\n覆盖率提升', BLUE_F, BLUE_E, bold=True),
    ]
    boxB = [
        box(ax, 75, ys[0], bw, bh, '问题：推理必然带来\n成本和耗时的上升', ORANGE_F, ORANGE_E),
        box(ax, 75, ys[1], bw, bh, '方式：先判断提问是否有效、\n有无候选技能，再按需推理', ORANGE_F, ORANGE_E),
        box(ax, 75, ys[2], bw, bh, '评测：计算每新增一个有效答案\n增加的计算成本，并折算人力', ORANGE_F, ORANGE_E),
        box(ax, 75, ys[3], bw, bh, '结果：增加的计算成本\n与节省的人力对照', ORANGE_F, ORANGE_E, bold=True),
    ]

    for col in (boxA, boxB):
        for x1, x2 in zip(col, col[1:]):
            arrow(ax, (x1[0], x1[1] + x1[3] / 2), (x2[0], x2[1] - x2[3] / 2))

    label(ax, 50, 106, '两个问题的答案，共同回答这套机制是否值得采用', fontsize=11.5, color='#555555')

    concBox = box(ax, 50, 118, 90, 13,
                   '结论：以增加的计算成本，换取更高的有效答案覆盖率和节省的人力',
                   GREEN_F, GREEN_E, fontsize=13, bold=True, wrap_width=36)

    arrow(ax, (boxA[3][0], boxA[3][1] + boxA[3][3] / 2), (36, concBox[1] - concBox[3] / 2),
          connectionstyle='arc3,rad=0.15', color='#1e8449')
    arrow(ax, (boxB[3][0], boxB[3][1] + boxB[3][3] / 2), (64, concBox[1] - concBox[3] / 2),
          connectionstyle='arc3,rad=-0.15', color='#1e8449')

    plt.tight_layout()
    plt.savefig('logic_chain_diagram.png', dpi=170, bbox_inches='tight', facecolor='white')
    print('saved: logic_chain_diagram.png')


if __name__ == '__main__':
    main()
