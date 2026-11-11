NO_ANSWER_TEXT = '未检索到答案'
AGENT_ERROR_TEXT = 'Agent执行异常'
NO_SKILL_TAG = 'NO_SKILL_MATCHED'
APPEND_NO_SKILL_TAG = True
KB_INVALID_KEYWORDS = (NO_ANSWER_TEXT, '未检索到相关信息')
SKILL_INVALID_KEYWORDS = (AGENT_ERROR_TEXT, NO_SKILL_TAG)


def normalize(value):
    if value is None:
        return ''
    return str(value).strip()


def contains_any(text, keywords):
    upper_text = text.upper()
    return any(k.upper() in upper_text for k in keywords)


def to_int(value):
    try:
        return int(float(normalize(value)))
    except (TypeError, ValueError):
        return None


def handler(params):
    kb_text = normalize(params.get("promptOut"))
    skill_text = normalize(params.get("skillResult"))
    skill_count = to_int(params.get("skillCount"))
    if skill_text and AGENT_ERROR_TEXT in skill_text:
        return AGENT_ERROR_TEXT
    if skill_text and not contains_any(skill_text, SKILL_INVALID_KEYWORDS):
        return skill_text
    if kb_text and not contains_any(kb_text, KB_INVALID_KEYWORDS):
        answer = kb_text
    else:
        answer = NO_ANSWER_TEXT
    if APPEND_NO_SKILL_TAG and skill_count == 0:
        return answer + "\n\n[" + NO_SKILL_TAG + "]"
    return answer
