import json

QUESTION_KEY = "question"
VALID = "VALID"
INVALID = "INVALID"
RETURN_REASON = False

MIN_EFFECTIVE_LEN = 2
MAX_SAME_CHAR_RUN = 4
FRAGMENT_LEN_RANGE = (2, 4)
MIN_FRAGMENT_REPEATS = 3
PURE_HUMAN_REQUESTS = (
    "人工", "转人工", "人工客服", "找人工", "要人工", "转人工客服",
    "客服", "在线客服", "找客服", "真人",
)

ZERO_WIDTH_CHARS = ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff")


def extract_question(raw):
    if raw is None:
        return ""
    text = str(raw).strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            data = json.loads(text)
            if isinstance(data, dict) and QUESTION_KEY in data:
                return str(data.get(QUESTION_KEY) or "")
        except ValueError:
            pass
    return text


def to_effective_text(text):
    chars = []
    for ch in text:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            ch = chr(code - 0xFEE0)
        elif code == 0x3000:
            ch = " "
        if ch in ZERO_WIDTH_CHARS:
            continue
        if ch.isalnum():
            chars.append(ch.lower())
    return "".join(chars)


def has_long_char_run(text):
    run = 0
    previous = ""
    for ch in text:
        if ch.isalpha() and ch == previous:
            run += 1
        else:
            run = 1
        previous = ch
        if run > MAX_SAME_CHAR_RUN:
            return True
    return False


def is_repeated_fragment(text):
    total = len(text)
    for size in range(FRAGMENT_LEN_RANGE[0], FRAGMENT_LEN_RANGE[1] + 1):
        if total % size == 0 and total // size >= MIN_FRAGMENT_REPEATS:
            if text == text[:size] * (total // size):
                return True
    return False


def check_rules(question):
    effective = to_effective_text(question)
    if not effective:
        return "EMPTY"
    if len(effective) <= MIN_EFFECTIVE_LEN:
        return "LEN_SHORT"
    if has_long_char_run(effective):
        return "REPEAT_CHAR"
    if is_repeated_fragment(effective):
        return "REPEAT_FRAGMENT"
    if effective in PURE_HUMAN_REQUESTS:
        return "HUMAN_ONLY"
    return None


def handler(params):
    try:
        question = extract_question(params.get(QUESTION_KEY))
        reason = check_rules(question)
    except Exception:
        return VALID
    if reason is None:
        return VALID
    if RETURN_REASON:
        return INVALID + "|" + reason
    return INVALID
