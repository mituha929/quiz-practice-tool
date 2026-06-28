import json


def load_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_answer(answer):
    return str(answer).replace(" ", "").replace(",", "").upper()


def validate_choice_question_bank(data):
    if not isinstance(data, list):
        raise ValueError("JSON 最外層必須是 list")
    if not data:
        raise ValueError("題庫不可為空")

    for idx, question in enumerate(data, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"第 {idx} 題必須是 object")

        for field in ["category", "question", "options", "answer"]:
            if field not in question:
                raise ValueError(f"第 {idx} 題缺少必要欄位：{field}")

        text = question["question"]
        if not isinstance(text, str) and not (
            isinstance(text, list) and all(isinstance(item, str) for item in text)
        ):
            raise ValueError(f"第 {idx} 題的 question 必須是字串或字串 list")

        options = question["options"]
        if not isinstance(options, dict) or not options:
            raise ValueError(f"第 {idx} 題的 options 必須是非空 object")

        if not isinstance(question["answer"], str):
            raise ValueError(f"第 {idx} 題的 answer 必須是字串")

        if "explanation" in question and not isinstance(question["explanation"], str):
            raise ValueError(f"第 {idx} 題的 explanation 必須是字串")

        option_keys = {str(key).upper() for key in options.keys()}
        answer_keys = set(normalize_answer(question["answer"]))
        if not answer_keys:
            raise ValueError(f"第 {idx} 題的 answer 不可為空")

        invalid_answers = answer_keys - option_keys
        if invalid_answers:
            invalid = ", ".join(sorted(invalid_answers))
            raise ValueError(f"第 {idx} 題的 answer 包含不存在於 options 的選項：{invalid}")


def validate_qa_question_bank(data):
    if not isinstance(data, list):
        raise ValueError("問答題 JSON 最外層必須是 list")

    required_fields = [
        "id",
        "category",
        "question_en",
        "question_zh",
        "answer_en",
        "answer_zh",
        "exam_focus",
    ]
    for idx, question in enumerate(data, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"第 {idx} 題必須是 object")
        for field in required_fields:
            if field not in question:
                raise ValueError(f"第 {idx} 題缺少必要欄位：{field}")


def index_categories(questions):
    indexed = {}
    for question in questions:
        category = question.get("category", "未分類")
        indexed.setdefault(category, []).append(question)
    return indexed


def import_question_bank(file_path):
    data = load_json_file(file_path)
    validate_choice_question_bank(data)
    return data
