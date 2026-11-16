RECORD_TYPE = "知识库未命中"


def normalize(value):
    if value is None:
        return ""
    return str(value).strip()


def handler(params):
    question = params.get("question")
    user = normalize(params.get("userName")) + "/" + normalize(params.get("sapId"))
    return [
        {
            "type": RECORD_TYPE,
            "question": question,
            "answer": "",
            "user": user,
            "supporter": "",
        }
    ]
