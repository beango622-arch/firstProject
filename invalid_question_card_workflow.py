TITLE = "编码通智能问答"
TITLE_COLOR = "#6975f7"
INVALID_QUESTION_TEXT = (
    "抱歉，未能识别到您的具体问题。"
    "请描述您遇到的问题，例如所在的功能页面、操作步骤和报错信息，以便为您解答。"
)


def handler(params):
    return [
        {
            "type": "title",
            "content": TITLE,
            "style": TITLE_COLOR,
        },
        {
            "type": "content",
            "list": [
                {
                    "type": [0],
                    "content": INVALID_QUESTION_TEXT,
                    "style": TITLE_COLOR,
                },
            ],
        },
    ]
