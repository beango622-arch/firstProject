# -*- coding: utf-8 -*-
"""生成重构后的创新奖申报材料（通用方案本体 + 编码通(新)案例）"""
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


FONT_BODY = '仿宋_GB2312'
FONT_HEAD = '黑体'
FONT_MONO = 'Consolas'


def set_run_font(run, name, size_pt, bold=False):
    run.font.name = name
    run.font.size = Pt(size_pt)
    run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rFonts = rpr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), name)


def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run(text)
    set_run_font(r, FONT_HEAD, 22, bold=True)
    return p


def add_h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    set_run_font(r, FONT_HEAD, 16, bold=True)
    return p


def add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    set_run_font(r, FONT_HEAD, 14, bold=True)
    return p


def add_body(doc, runs):
    """runs: list of (text, bold) tuples"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    for text, bold in runs:
        r = p.add_run(text)
        set_run_font(r, FONT_BODY, 12, bold=bold)
    return p


def add_note(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    set_run_font(r, FONT_BODY, 10.5, bold=False)
    return p


def add_quote(doc, body, source):
    def style(p, space_after):
        pPr = p._p.get_or_add_pPr()
        border = OxmlElement('w:pBdr')
        left = OxmlElement('w:left')
        left.set(qn('w:val'), 'single')
        left.set(qn('w:sz'), '18')
        left.set(qn('w:space'), '10')
        left.set(qn('w:color'), '9E9E9E')
        border.append(left)
        pPr.append(border)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.right_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(space_after)

    p = doc.add_paragraph()
    style(p, 2)
    set_run_font(p.add_run(body), FONT_BODY, 11)
    p2 = doc.add_paragraph()
    style(p2, 10)
    set_run_font(p2.add_run(source), FONT_BODY, 10)
    return p


def add_image(doc, path, width_inches, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run()
    run.add_picture(path, width=Inches(width_inches))
    if caption:
        add_note(doc, caption)


def add_placeholder(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    set_run_font(r, FONT_BODY, 11, bold=True)
    return p


def add_mono_block(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if i > 0:
            p.add_run().add_break()
        r = p.add_run(line)
        set_run_font(r, FONT_MONO, 10, bold=False)
    return p


def add_bullet(doc, runs):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(8)
    for text, bold in runs:
        r = p.add_run(text)
        set_run_font(r, FONT_BODY, 12, bold=bold)
    return p


def add_table(doc, header, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.style = 'Table Grid'
    for j, h in enumerate(header):
        cell = t.rows[0].cells[j]
        p = cell.paragraphs[0]
        r = p.add_run(h)
        set_run_font(r, FONT_BODY, 11, bold=True)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            p = cell.paragraphs[0]
            r = p.add_run(val)
            set_run_font(r, FONT_BODY, 11, bold=False)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def build():
    doc = docx.Document()

    add_title(doc, '智能技术支持问答体系——低代码产品矩阵中的落地实践\n(核心落地案例：编码通(新))')

    # ============ 一、定义问题 ============
    add_h1(doc, '一、定义问题')

    add_h2(doc, '1.1 行业背景与通用诉求')
    add_body(doc, [('当前，企业构建智能客服系统，普遍以知识库检索作为基础能力：将常见问题沉淀为知识库，由系统根据用户提问进行匹配应答。该方式成本较低、响应迅速，能够较好地覆盖标准化问题。然而，面对复杂业务场景，仅依赖知识库检索已难以满足实际需要。', False)])
    add_body(doc, [('行业研究表明，仅依靠检索既有内容，相当比例的问题无法得到有效解答。Gartner的一项调研显示：', False)])
    add_quote(doc,
              '对5,728位客户的调研发现，只有14%的客户服务问题能在自助渠道中完全解决；即使是客户认为"非常简单"的问题，也只有36%。自助失败最常见的原因，是客户找不到与问题相关的内容（43%）；另有45%从自助渠道开始的客户表示，企业没有理解他们想解决什么问题。',
              '来源：Gartner新闻稿《Gartner Survey Finds Only 14% of Customer Service Issues Are Fully Resolved in Self-Service》，2024年8月19日发布（调研于2023年12月进行，覆盖所有自助渠道，不限于聊天机器人）')
    add_body(doc, [('解决此类问题，需要系统结合用户的具体情况进行推理，而不能仅限于内容检索。但推理的响应耗时和token消耗均明显高于检索，难以对全部问题采用。因此，业界较为通行的做法是分层处理：简单问题采用轻量方式应答，复杂问题再交由更强的推理能力处理，并以"解决单个问题的实际成本"而非单次调用价格来衡量成效。', False)])
    add_body(doc, [('在技术支持场景下，这一问题更为突出。用户咨询多集中于具体业务的操作与配置，同一问题在不同用户的数据结构下，答案往往不同，知识库中的既有答案常常无法满足需要，必须依靠推理。而推理意味着对模型计算资源提出更高的需求，由此产生了如何使计算资源得到高效利用的问题。如何在具备推理能力的同时，将计算资源用于真正需要的问题，是本体系需要解决的核心问题。', False)])

    add_h2(doc, '1.2 技术支持场景的共性问题')
    add_body(doc, [('对实际的技术支持咨询记录进行梳理后发现，这类场景普遍存在三个问题：', False)])
    add_body(doc, [('问题一：用户咨询的问题类型不一，单一的应答方式难以覆盖。', True), ('有的问题答案固定，有的需要结合用户自身的业务和数据才能回答，还有的并不属于提问。据此，咨询可分为四类：', False)])

    add_table(doc,
              ['问题类型', '说明', '占比'],
              [
                  ['确定性问题', '答案固定，依据标准知识即可回答', '27.7%'],
                  ['推理性问题', '解决思路固定，但需要结合用户的业务场景和数据结构，才能给出有针对性的答案', '68.2%'],
                  ['场景可行性评估', '用户需要了解某一业务场景能否实现，涉及复杂的业务判断，规则和模板难以覆盖', '3.6%'],
                  ['需求/BUG反馈', '用户提出的产品改进建议或缺陷反馈，不属于问答范畴', '0.4%'],
              ])
    add_note(doc, '说明：占比数据来自低代码场景近期历史咨询会话的统计，分类由AI辅助完成。')
    add_body(doc, [('其中，推理性问题占比接近七成。仅依靠检索既有知识，这部分问题难以得到有针对性的解答。', False)])

    add_body(doc, [('问题二：响应速度与答案质量难以兼顾。', True), ('关键词匹配等方式响应迅速，但答案质量有限。若要使答案准确、贴合用户的具体情况，就需要进行推理，而推理会带来更高的成本和更长的等待时间。如何在两者之间取得平衡，是各类问答系统都需要面对的问题。', False)])
    add_body(doc, [('问题三：哪些事项由机器承担，哪些事项由人工负责，需要明确。', True), ('部分问题涉及复杂的业务判断，需要有经验的人员把关；知识库和技能库应当补充哪些内容，也需要人员结合业务作出判断。人的经验在技术支持中始终具有价值。体系的目标不是排除人工，而是明确人工应当承担的事项，使人的时间投入到最有价值的环节。', False)])

    # ============ 二、方案设计 ============
    add_h1(doc, '二、方案设计：智能技术支持问答体系')
    add_body(doc, [('这一章介绍针对上面三个问题设计的问答体系。核心流程是固定的，知识库内容和SKILL清单是可配置的业务数据，两者分开维护。实际使用情况见第三章。', False)])

    add_h2(doc, '2.1 设计理念：三条核心价值主张')
    add_body(doc, [('针对1.2所述的三个问题，本体系确立了三条核心价值主张：', False)])
    add_body(doc, [('价值主张一：分层应答，因题施策。', True), ('按问题性质分层处理：先检索知识库；需要结合用户具体情况的问题，交由Agent进行推理；仍无法解决的，推荐相关文档；最终由人工接手处理。同时，体系能够自动发现知识库和技能库中的缺口，交由人工补充。目标是将"人工被动答疑"转变为"机器分层应答，人工专注于高价值问题"。', False)])
    add_body(doc, [('价值主张二：按需推理，渐进交付。', True), ('上游先判断是否存在可用的技能，存在时才触发下游执行。知识库答案与技能答案分阶段交付给用户，并根据两者的状态判断是否已得到最终答案。这样，有限的计算资源集中用于真正需要推理的问题，用户也无需面对空白界面长时间等待。', False)])
    add_body(doc, [('价值主张三：人机协同，价值聚焦。', True), ('体系有意保留了人工节点，这是主动的设计选择。复杂的场景判断，以及知识库和技能库的治理，都需要依靠人的经验和业务判断，这正是人工在体系中的价值所在。体系的作用，是让人的时间用于这些环节，而不是被大量常规问题占用。', False)])

    add_h2(doc, '2.2 整体架构')
    add_body(doc, [('系统分四个阶段：预处理、核心应答、渐进交付与人工协同、知识自增长。各阶段的流程和具体业务内容是分开的，知识库、SKILL清单、文档库都是可配置的数据。图里保留了两个人工环节，这是我们主动做的设计：复杂的场景判断，以及知识库和技能库的治理，都需要人的经验。', False)])
    add_image(doc, 'architecture_diagram.png', 5.0, caption='图1 整体架构图：两个人工入口、核心应答链路和知识自增长闭环')

    add_h2(doc, '2.3 问题预处理：查询标准化与提问有效性过滤')
    add_body(doc, [('用户提问往往很口语化，直接拿去检索，容易搜不到想要的内容。所以系统先让大模型把问题改写成书面化的标准问句，再去检索。同时还有一层提问有效性过滤：规则层先过滤明显无效的内容，语义层再判断是不是真的包含问题、报错或阻碍。两层都通过的提问，才计入熔断计时。具体规则这里不展开，避免被人针对性绕过。', False)])

    add_h2(doc, '2.4 核心引擎：三级递进应答与人工入口动态管控')
    add_body(doc, [('（1）三级应答能力', True)])
    add_body(doc, [('第一级·知识库检索：', True), ('对接企业知识库做向量检索，知识库内容可配置。检索完成后，系统才会针对当前问题判断有没有可用的技能（见(2)），两步严格先后、不并行，因为终态判断要依赖知识库答案这个前置结果。', False)])
    add_body(doc, [('第二级·Agent技能推理：', True), ('需要结合用户具体业务场景才能回答的问题，由双Agent架构（见(2)）判断并执行可用的技能。', False)])
    add_body(doc, [('第三级·文档推荐：', True), ('前两级都没有结果时，按关键词推荐相关文档，不让用户看到空白的回复。', False)])
    add_body(doc, [('机器人给出的答案会同时展示知识来源，方便溯源，同一个对话里也可以多轮追问。', False)])

    add_body(doc, [('（2）双Agent：上游做决策，下游只执行', True)])
    add_body(doc, [('技能推理为什么要拆成两个Agent，而不是让一个Agent判断完直接执行？原因在渐进交付（见(3)）。系统要尽早知道有没有可用的技能：有，就告诉用户更准的答案在路上；没有，知识库的答案就是最终答案。拿不到这个信号，要么把还没做完的答案当成最终答案，要么让用户干等着。判断有没有技能只要做一次轻量的语义匹配，执行技能却要真正跑一遍，耗时长得多。两件事放在一个Agent里，就得等执行完才知道有没有技能，渐进交付也就做不成了。所以我们把它拆成上游和下游两个Agent，上游快速给出判断，下游专心执行。', False)])
    add_bullet(doc, [('上游·技能决策Agent：', True), ('只负责语义判断。它识别用户的一个或最多两个子需求，每个子需求按"技能描述覆盖的业务范围是否和需求相符"，匹配一个最合适的技能，最后给出一份下游可以直接执行的技能清单，不需要再判断一遍。', False)])
    add_bullet(doc, [('下游·技能执行Agent：', True), ('不再做语义判断，按清单逐个执行（技能名称相似度达到90%以上的表述差异可以容忍）。只有技能确实不存在，或者调用后没有有效结果，才判定无法执行。', False)])
    add_body(doc, [('这样分工是根据真实运行情况调出来的。早期上下游各自判断，下游会对上游已经确认的技能重新产生怀疑，倾向于保守地拒绝执行，多层判断叠在一起，误判反而更多。改成上游一个点决策、下游只执行以后，决策更一致，命中率也提高了。具体的SKILL清单属于可配置的业务数据，和双Agent的协作方式本身没有关系。为什么选这种架构、代价是什么，见第三章。', False)])

    add_body(doc, [('（3）人工入口动态管控', True)])
    add_body(doc, [('微观：', True), ('答案分阶段交给用户：先是知识库答案或等待提示，然后是技能答案，最后是文档兜底。要不要展示人工支持按钮，取决于是不是到了终态，而终态由知识库检索结果和候选技能是否存在这两个条件的组合来判断：', False)])
    add_table(doc,
              ['知识库检索结果', '候选技能是否存在', '是否终态', '后续处理'],
              [
                  ['有答案', '不存在', '是', '直接展示知识库答案，提供人工支持按钮'],
                  ['有答案', '存在', '否', '知识库答案作为过渡参考，触发技能执行Agent，暂不提供人工支持按钮'],
                  ['无答案', '存在', '否', '展示等待提示，触发技能执行Agent，暂不提供人工支持按钮'],
                  ['无答案', '不存在', '否', '展示等待提示，跳过技能执行，直接进入文档推荐兜底，暂不提供人工支持按钮'],
              ])
    add_note(doc, '说明：技能执行完成，或者文档推荐兜底返回之后，不管结果怎样，都算到了终态，这时统一提供人工支持按钮。这样既避免用户看到一个质量一般的中间答案就转向人工，也避免用户在不知情的情况下一直等。')
    add_body(doc, [('该机制的实际运行效果见第三章。', False)])
    add_body(doc, [('宏观：', True), ('用户如果1小时内没向机器人提过问，就直接想找人工，会先被引导向机器人提问。熔断规则的参数可以配置。', False)])
    add_body(doc, [('这套机制自然形成了一个可以统计的问题漏斗（总提问数、自主解决数、转人工数），具体见第三章。', False)])

    add_body(doc, [('（4）结构化输出协议', True)])
    add_body(doc, [('另外设计了结构化的Agent输出格式，解析时带异常兜底，能处理大模型输出格式不对、或者返回"未检索到相关信息"这类无效答案的情况。这样大模型的输出再不稳定，也不会影响后面固定的流程。', False)])

    add_h2(doc, '2.5 知识自增长闭环：缺口识别与人工补齐')
    add_body(doc, [('"一次对话值不值得沉淀""该补知识库还是补技能"，这类判断需要结合业务经验，我们交给人来做。为此设计了两条互补的路径：', False)])
    add_body(doc, [('路径A·机器发现缺口：', True), ('直接用核心引擎已经算出的两个信号，也就是知识库有没有命中、有没有候选技能，把存在能力缺口的问题按组合情况分级放进问题池，由支持团队定期review，有针对性地补齐。问题池暂时只分级，不做去重聚合，聚合去重是下一步的计划，见四、总结。', False)])
    add_body(doc, [('路径B·人工主动沉淀：', True), ('支持人员在处理问题时，可以用快捷指令把有价值的对话沉淀成知识库QA，或者记录产品需求和BUG反馈。', False)])
    add_body(doc, [('两条路径分工很清楚：机器负责发现缺口，人负责决定怎么补、并且补上。', False)])

    # ============ 三、实践成效 ============
    add_h1(doc, '三、实践成效')
    add_body(doc, [('上线前，所有咨询都由人工处理。上线后，机器人的问题自主解决率达到【XX】%，这部分问题不再占用人工。', True)])
    add_body(doc, [('这套体系已在低代码产品矩阵内使用，下面的数据来自其中的编码通(新)，依次是自主解决情况、机制验证（包括架构选型的依据）、响应效率和能力建设。', False)])

    add_h2(doc, '3.1 自主解决率与问题漏斗')
    add_body(doc, [('总提问数、机器人自主解决数和转人工数构成一个问题漏斗，我们用它统计机器人实际解决了多少问题：', False)])
    add_table(doc,
              ['指标', '数值'],
              [
                  ['总提问数', '【待补充】'],
                  ['机器人自主解决数', '【待补充】'],
                  ['转人工支持数', '【待补充】'],
                  ['自主解决率', '【待补充】'],
              ])
    add_note(doc, '口径说明：用户没有触发人工支持，就算机器人自主解决。目前还没有结合用户满意度来判断，详见四、总结的展望部分。')

    add_h2(doc, '3.2 渐进交付机制的验证')
    add_body(doc, [('评测说明：', True), ('本节数据来自近期一段时间内自然产生的全量咨询会话日志，没有经过人工倾向性筛选，共提取233条有效会话。', False)])
    add_note(doc, '说明：这是阶段性的评测范围，正式提交前会视时间情况扩大样本，让结论更稳。')
    add_body(doc, [('候选技能送达率：', True), ('存在候选技能的183个会话里，最终送达技能答案的比例是67.2%。按知识库检索结果拆开看：知识库有答案且存在候选技能的93个会话，送达率73.1%；知识库没有答案但存在候选技能的90个会话，送达率61.1%。', False)])
    add_table(doc,
              ['统计口径', '候选技能会话数', '送达成功数', '送达率'],
              [
                  ['整体（全部候选技能会话）', '183', '123', '67.2%'],
                  ['知识库有答案 + 候选技能存在', '93', '68', '73.1%'],
                  ['知识库无答案 + 候选技能存在', '90', '55', '61.1%'],
              ])
    add_body(doc, [('答案质量判断：', True), ('在"知识库有答案、技能答案也成功送达"的68个会话里，我们进一步比较了两个答案的实质差异：', False)])
    add_table(doc,
              ['判断结果', '占比'],
              [
                  ['技能答案更优', '79.4%'],
                  ['两者相当', '10.3%'],
                  ['技能答案未见明显提升', '10.3%'],
                  ['技能答案存在错误或偏题', '0.0%'],
              ])
    add_note(doc, '方法说明：答案质量由大模型按统一的提示词，比较知识库答案和技能答案的实质信息差异并给出判断。68个会话都完成了评审，没有发现技能答案存在事实错误或答偏的情况。这是当前统一评审口径下的阶段性结果，还没有用人工专家标注作为独立的标准。')
    add_body(doc, [('核心结论：', True), ('综合送达率和质量判断，在"知识库有答案、候选技能也存在"的93个会话里，终态判断最终把58.1%（54/93）转化成了真正更优的技能答案。如果采用"知识库优先"的策略，这些场景下更优答案的送达比例是0%。', False)])

    add_body(doc, [('补充说明：这些数据也是架构选型的依据。', True), ('技能推理这一步，我们在设计时比较过三种方案：知识库优先、技能优先、双Agent分段式（当前方案）。上面的验证数据，再加上一组成本测试，就是当时做取舍的依据。这部分是方案选型过程中的推理验证，不属于上线后的运营成效。下图是整体思路，后面按方案逐个说明。', False)])
    add_image(doc, 'logic_chain_diagram.png', 6.3, caption='图2 架构选型的论证思路：左边说明为什么要有技能推理，右边说明为什么要拆成两个Agent')
    add_body(doc, [('为何不是知识库优先：', True), ('这种策略下，知识库一旦命中就直接当最终答案返回，不再判断有没有候选技能。按上面的数据，93个"知识库有答案、候选技能也存在"的会话里，那54个本该送到用户手里的更优答案（占58.1%）会全部错过。', False)])
    add_body(doc, [('为何不是技能优先：', True), ('这种策略跳过候选技能判断，所有问题都直接去执行技能。对本来就没有可用技能的问题，执行环节是白跑一趟，浪费计算资源。按单Agent平均每次调用的成本粗略估算，评测样本里50个没有候选技能的会话，会多消耗约109万token、约64分钟的无效计算。', False)])
    add_body(doc, [('为何是双Agent分段式，成本能不能接受：', True), ('双Agent比单Agent总耗时多了约71.3%，总Token消耗多了约288.4%。这笔成本换来的是渐进交付能做起来：判断和执行不拆开，就没法提前知道有没有可用的技能。从上面的数据看是值得的：54个更好的答案送到了用户手里，评审的68个会话里技能答案没有出现错误。也可以这么理解，这些额外成本买的是"提前知道有没有更好的答案"。不花这笔钱，这54个答案还是送不出去。', False)])
    add_note(doc, '说明：双Agent与单Agent的成本对比，取自66个问题的配对对比，同一个问题分别用两种架构跑批。')

    add_h2(doc, '3.3 响应效率与人力成本')
    add_note(doc, '口径说明：本节的上线前后数据，反映的是整套智能技术支持问答体系的综合运营效果，不把所有效果都算在双Agent架构头上。终态判断和双Agent本身带来的增量价值，在3.2里单独验证。')
    add_table(doc,
              ['指标', '上线前', '上线后'],
              [
                  ['平均响应/关单时长', '约50分钟', '【待补充】'],
                  ['日均人工支持投入', '4人力全天候', '【待补充】'],
                  ['日均问题处理量', '【待补充】', '【待补充】'],
              ])

    add_h2(doc, '3.4 知识沉淀能力建设情况')
    add_table(doc,
              ['能力项', '建设情况'],
              [
                  ['QA沉淀链路', '已打通，支持人员可通过快捷指令一键沉淀'],
                  ['需求/BUG反馈记录链路', '已打通，与QA沉淀共用同一快捷指令入口'],
                  ['Skill能力库', '已构建，覆盖7大业务模块，约30个SKILL'],
                  ['未解决问题池（分级收纳）', '已构建并自动运行，暂不做聚合去重'],
                  ['知识库QA条目数（累计）', '沉淀量仍在积累中'],
              ])
    add_note(doc, '说明：目前是否值得沉淀，要靠支持人员主观判断，存在触发门槛，这是我们认为需要重点优化的地方（见四、总结的展望）。')
    add_note(doc, '评价口径：知识沉淀是长期的能力建设，现阶段主要看链路有没有打通、缺口能不能持续进入治理流程，不只用短期新增的条目数来衡量。')

    # ============ 四、总结 ============
    add_h1(doc, '四、总结')

    add_h2(doc, '4.1 创新性')
    add_bullet(doc, [('用数据做架构选型：', True), ('技能推理这一步有三种方案可选，我们没有凭经验拍板，而是用真实会话做了两组评测：一组看终态判断能不能把更好的答案送到用户手里，一组看拆成双Agent多花了多少成本（见3.2）。把判断和执行拆开本身不算新鲜，我们觉得更有价值的是这个选型过程，每个取舍都有数据支撑，当前方案多花的成本也如实写了出来。', False)])
    add_bullet(doc, [('按问题性质分层应答：', True), ('我们把咨询分成确定性、推理性、场景可行性评估、需求反馈四类，设计了知识库检索、Agent技能推理、文档兜底逐层应答的方式，让不同性质的问题各走合适的路径，不再是传统FAQ机器人"查得到才能答"的样子。', False)])
    add_bullet(doc, [('在资源效率和用户体验之间找平衡：', True), ('终态判断由知识库状态和候选技能状态共同决定，用它控制渐进交付的每一步要不要开放人工入口。再加上熔断时间窗口和提问有效性过滤两道宏观控制，让这个平衡既能落地，也不容易被人故意绕过。', False)])
    add_bullet(doc, [('双Agent单点决策：', True), ('早期上下游各自判断，我们在实际运行中发现多层独立判断会把误判叠加放大，于是收敛成上游一个点决策、下游只执行，命中率和一致性都改善了。', False)])
    add_bullet(doc, [('知识库和技能库自己长：', True), ('机器直接利用链路里已有的信号，自动发现知识库和技能的缺口并分级收纳，人工在支持过程中顺手沉淀，两条路径互补，知识库和技能库随着系统运行不断补充。', False)])
    add_bullet(doc, [('核心流程与业务数据分开：', True), ('核心引擎和Agent协同流程保持不变，知识库、SKILL清单作为可配置的业务数据单独维护。这套体系目前已在低代码产品矩阵内使用。', False)])

    add_h2(doc, '4.2 效果和沉淀')
    add_body(doc, [('这套体系的价值体现在三个方面。运营上，机器人自主解决了一部分用户问题，缩短了响应链路，减轻了人工压力（见3.1、3.3）。架构上，终态判断和双Agent分段式响应让更多问题拿到了更好的答案，代价是可以量化的成本增加（见3.2）。能力上，我们沉淀了覆盖7大业务模块、约30个SKILL的推理能力库，打通了缺口发现和人工补充的链路，这套体系目前已在低代码产品矩阵内使用（见3.4）。项目研发投入：【待补充具体人力与周期投入数据】。', False)])

    add_h2(doc, '4.3 展望')
    add_bullet(doc, [('持续优化人和机器的分工：', True), ('人工节点是我们有意保留的部分。后续会根据运行数据，看哪些问题人工介入最有价值，让人的精力更集中在这些地方，同时把能标准化的部分沉淀下来，减少人在重复问题上的消耗。', False)])
    add_bullet(doc, [('持续统计问题分层数据：', True), ('计划用AI辅助分类，持续统计历史和新增的咨询，让"问题分层"一直有数据支撑，反过来指导架构优化。', False)])
    add_bullet(doc, [('优化知识沉淀的触发方式：', True), ('现在人工沉淀靠支持人员自己判断，有触发门槛。后续想试试让AI自动识别有价值的对话并推荐沉淀，同时建立沉淀贡献的激励机制。', False)])
    add_bullet(doc, [('完善满意度埋点：', True), ('目前触发人工支持就视为机器人没有自主解决，还没有对答案满意度做细致的埋点，后续计划加上显式的反馈机制。', False)])
    add_bullet(doc, [('丰富熔断策略：', True), ('现在熔断只有"1小时内没提问就不能直接呼叫人工"这一条规则，后续想结合更多场景，比如同一问题的重复追问次数，丰富熔断和引导的策略。', False)])
    add_bullet(doc, [('优化转人工的体验：', True), ('现在转人工时，机器人这边的对话上下文不会自动同步给人工客服，后续计划打通，避免用户重复描述问题。', False)])
    add_bullet(doc, [('问题池聚合去重和摘要推送：', True), ('现在问题池只分级，不做相似问题的去重聚合。后续计划用向量聚合，按频次和等级排序，定期推送摘要，并探索缺口补上之后的自动验证。', False)])

    out_path = '编码通新智能问答支持系统-创新奖申报材料.docx'
    doc.save(out_path)
    print('saved:', out_path)


if __name__ == '__main__':
    build()
