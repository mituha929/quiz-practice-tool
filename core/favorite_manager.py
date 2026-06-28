import json
from pathlib import Path


class FavoriteManager:
    def __init__(self, favorite_path=Path("user_data") / "favorites" / "favorite_questions.json"):
        self.favorite_path = Path(favorite_path)

    def load_favorites(self):
        if not self.favorite_path.exists():
            return []
        try:
            with open(self.favorite_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def add_favorite(self, question):
        favorites = self.load_favorites()
        key = self._question_key(question)
        if any(item.get("question_id") == key for item in favorites):
            return favorites, False

        favorites.append({
            "question_id": key,
            "category": question.get("category", "未分類"),
            "question_data": question,
        })
        self.favorite_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.favorite_path, "w", encoding="utf-8") as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
        return favorites, True

    def _question_key(self, question):
        return str(question.get("id") or f"{question.get('category', '')}|{question.get('question', '')}")
