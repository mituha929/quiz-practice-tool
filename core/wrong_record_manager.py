import json
from datetime import datetime
from pathlib import Path


DEFAULT_WRONG_OUTPUT_DIR = Path("錯誤題目") / "錯誤題目題號"
DEFAULT_WRONG_FILE_NAME = "wrong_questions_record.json"


class WrongRecordManager:
    def __init__(self, output_dir=DEFAULT_WRONG_OUTPUT_DIR, file_name=DEFAULT_WRONG_FILE_NAME):
        self.output_dir = Path(output_dir)
        self.file_name = self._ensure_json_suffix(file_name)

    def _ensure_json_suffix(self, file_name):
        return file_name if str(file_name).lower().endswith(".json") else f"{file_name}.json"

    def get_output_path(self):
        return self.output_dir / self.file_name

    def set_output_folder(self, folder_path):
        self.output_dir = Path(folder_path)

    def set_output_file_name(self, file_name):
        self.file_name = self._ensure_json_suffix(file_name)

    def load_wrong_records(self):
        path = self.get_output_path()
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_wrong_records(self, wrong_questions, existing_records=None):
        records_by_key = {}
        for record in existing_records or self.load_wrong_records():
            records_by_key[self._record_key(record)] = record

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in wrong_questions:
            question = item["question"]
            key = self._question_key(question)
            old_record = records_by_key.get(key, {})
            records_by_key[key] = {
                "question_id": str(question.get("id") or key),
                "category": question.get("category", "未分類"),
                "question": question.get("question", ""),
                "options": question.get("options", {}),
                "question_data": question,
                "user_answer": item.get("user_answer", []),
                "correct_answer": item.get("correct_answer", []),
                "explanation": question.get("explanation", "無"),
                "wrong_count": int(old_record.get("wrong_count", 0)) + 1,
                "last_wrong_at": now,
            }

        records = list(records_by_key.values())
        self._write_records(records)
        return records

    def clear_wrong_records(self):
        self._write_records([])

    def export_wrong_records(self, output_dir=None, file_name=None):
        target_dir = Path(output_dir) if output_dir else self.output_dir
        target_name = self._ensure_json_suffix(file_name or self.file_name)
        target_path = target_dir / target_name
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.load_wrong_records(), f, ensure_ascii=False, indent=2)
        return target_path

    def _write_records(self, records):
        path = self.get_output_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def _record_key(self, record):
        question_data = record.get("question_data", record)
        return self._question_key(question_data)

    def _question_key(self, question):
        return str(question.get("id") or f"{question.get('category', '')}|{question.get('question', '')}")
