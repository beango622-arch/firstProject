# -*- coding: utf-8 -*-
"""生成"4.1 方案论证逻辑回顾"配套的逻辑链示意图"""
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
    ax.set_ylim(0, 168)
    ax.invert_yaxis()
    ax.axis('off')

    label(ax, 50, 4, '架构选型的论证思路', fontsize=18, color='#1a1a1a')
    label(ax, 25, 13, '为什么要有技能推理', fontsize=12.5, color='#1f5fa8')
    label(ax, 75, 13, '为什么要拆成两个Agent', fontsize=12.5, color='#b5651d')

    BLUE_F, BLUE_E = '#e8f1fb', '#1f5fa8'
    ORANGE_F, ORANGE_E = '#fdf1e6', '#b5651d'
    AMBER_F, AMBER_E = '#fff4da', '#c9962b'
    RED_F, RED_E = '#fbe9e7', '#c0392b'
    GREEN_F, GREEN_E = '#e8f6ee', '#1e8449'

    bw, bh = 40, 16
    yA = [24, 47, 70, 93]
    yB = [24, 47, 70, 93]

    boxA1 = box(ax, 25, yA[0], bw, bh,
                '问题一：推理性问题占68.2%，光靠知识库检索答不好', BLUE_F, BLUE_E)
    boxA2 = box(ax, 25, yA[1], bw, bh,
                '需要Agent技能推理，补上知识库答不了的部分', BLUE_F, BLUE_E)
    boxA3 = box(ax, 25, yA[2], bw, bh,
                '实测：知识库已有答案时，技能答案79.4%更好，0%出错', BLUE_F, BLUE_E)
    boxA4 = box(ax, 25, yA[3], bw, bh,
                '结论：技能推理确实带来了更好的答案', BLUE_F, BLUE_E, bold=True)

    boxB1 = box(ax, 75, yB[0], bw, bh,
                '问题二：答得快和答得好\n很难兼得', ORANGE_F, ORANGE_E)
    boxB2 = box(ax, 75, yB[1], bw, bh,
                '所以分阶段交付答案：不干等执行完，也不只给知识库答案', ORANGE_F, ORANGE_E)
    boxB3 = box(ax, 75, yB[2], bw, bh,
                '分阶段交付要求：要提前知道有没有候选技能', ORANGE_F, ORANGE_E)
    boxB4 = box(ax, 75, yB[3], bw, bh,
                '结论：拆成两个Agent，上游判断，下游执行', ORANGE_F, ORANGE_E, bold=True)

    for x1, x2 in [(boxA1, boxA2), (boxA2, boxA3), (boxA3, boxA4)]:
        arrow(ax, (x1[0], x1[1] + x1[3] / 2), (x2[0], x2[1] - x2[3] / 2))
    for x1, x2 in [(boxB1, boxB2), (boxB2, boxB3), (boxB3, boxB4)]:
        arrow(ax, (x1[0], x1[1] + x1[3] / 2), (x2[0], x2[1] - x2[3] / 2))

    label(ax, 50, 106, '两条线各自成立，一起指向同一个架构', fontsize=11.5, color='#555555')

    costBox = box(ax, 50, 118, 86, 15,
                   '代价：相比单Agent，总耗时 +71.3%，总Token消耗 +288.4%',
                   AMBER_F, AMBER_E, fontsize=12.5, bold=True, wrap_width=30)

    arrow(ax, (boxA4[0], boxA4[1] + boxA4[3] / 2), (36, costBox[1] - costBox[3] / 2), connectionstyle='arc3,rad=0.15')
    arrow(ax, (boxB4[0], boxB4[1] + boxB4[3] / 2), (64, costBox[1] - costBox[3] / 2), connectionstyle='arc3,rad=-0.15')

    cBw, cBh, yC = 40, 19, 137
    compC1 = box(ax, 25, yC, cBw, cBh,
                  '如果用"知识库优先"：93个会话里，58.1%本该送达的更好答案会全部错过', RED_F, RED_E)
    compC2 = box(ax, 75, yC, cBw, cBh,
                  '如果用"技能优先"：50个没有候选技能的会话白跑一趟，约浪费109万Token、64分钟', RED_F, RED_E)

    arrow(ax, (costBox[0] - 10, costBox[1] + costBox[3] / 2), (compC1[0], compC1[1] - compC1[3] / 2), connectionstyle='arc3,rad=-0.1')
    arrow(ax, (costBox[0] + 10, costBox[1] + costBox[3] / 2), (compC2[0], compC2[1] - compC2[3] / 2), connectionstyle='arc3,rad=0.1')

    concBox = box(ax, 50, 159, 90, 14,
                   '结论：三种方案里，只有双Agent分段式既能送出更好的答案，又不浪费资源',
                   GREEN_F, GREEN_E, fontsize=13, bold=True, wrap_width=30)

    arrow(ax, (compC1[0], compC1[1] + compC1[3] / 2), (40, concBox[1] - concBox[3] / 2), connectionstyle='arc3,rad=0.12', color='#1e8449')
    arrow(ax, (compC2[0], compC2[1] + compC2[3] / 2), (60, concBox[1] - concBox[3] / 2), connectionstyle='arc3,rad=-0.12', color='#1e8449')

    plt.tight_layout()
    plt.savefig('logic_chain_diagram.png', dpi=170, bbox_inches='tight', facecolor='white')
    print('saved: logic_chain_diagram.png')


if __name__ == '__main__':
    main()
