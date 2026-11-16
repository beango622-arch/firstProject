import json
import re
import unicodedata

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

ZERO_WIDTH_PATTERN = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
SAME_CHAR_RUN_PATTERN = re.compile(r"([^\W\d_])\1{%d,}" % MAX_SAME_CHAR_RUN)
FRAGMENT_PATTERN = re.compile(
    r"^(.{%d,%d}?)\1{%d,}$" % (FRAGMENT_LEN_RANGE[0], FRAGMENT_LEN_RANGE[1], MIN_FRAGMENT_REPEATS - 1)
)


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
    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH_PATTERN.sub("", text).lower()
    return "".join(ch for ch in text if unicodedata.category(ch)[0] in ("L", "N"))


def check_rules(question):
    effective = to_effective_text(question)
    if not effective:
        return "EMPTY"
    if len(effective) <= MIN_EFFECTIVE_LEN:
        return "LEN_SHORT"
    if SAME_CHAR_RUN_PATTERN.search(effective):
        return "REPEAT_CHAR"
    if FRAGMENT_PATTERN.match(effective):
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
