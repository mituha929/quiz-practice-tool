import json
from pathlib import Path


class QuizHistoryManager:
    def __init__(self, history_path=Path("user_data") / "quiz_history" / "quiz_history.json"):
        self.history_path = Path(history_path)

    def load_history(self):
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def add_history(self, record):
        history = self.load_history()
        history.insert(0, record)
        history = history[:10]
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return history

    def clear_history(self):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
