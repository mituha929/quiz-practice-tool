import json
from pathlib import Path


class FavoriteManager:
    DEFAULT_CATEGORY = "已收藏的題目"

    def __init__(self, favorite_path=Path("user_data") / "favorites" / "favorite_questions.json"):
        self.favorite_path = Path(favorite_path)
        self.category_path = self.favorite_path.with_name("favorite_categories.json")

    def load_favorites(self):
        if not self.favorite_path.exists():
            return []
        try:
            with open(self.favorite_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def load_categories(self):
        categories = [self.DEFAULT_CATEGORY]
        if self.category_path.exists():
            try:
                with open(self.category_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    categories.extend(str(item).strip() for item in data if str(item).strip())
            except Exception:
                pass
        return list(dict.fromkeys(categories))

    def save_categories(self, categories):
        clean_categories = []
        for item in categories:
            name = str(item).strip()
            if name and name not in clean_categories:
                clean_categories.append(name)
        if self.DEFAULT_CATEGORY not in clean_categories:
            clean_categories.insert(0, self.DEFAULT_CATEGORY)
        self.category_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.category_path, "w", encoding="utf-8") as f:
            json.dump(clean_categories, f, ensure_ascii=False, indent=2)
        return clean_categories

    def add_category(self, category_name):
        name = str(category_name).strip()
        if not name:
            return self.load_categories(), False
        categories = self.load_categories()
        if name in categories:
            return categories, False
        categories.append(name)
        return self.save_categories(categories), True

    def group_favorites_by_category(self, favorites=None):
        grouped = {}
        for item in favorites if favorites is not None else self.load_favorites():
            category = item.get("favorite_category") or self.DEFAULT_CATEGORY
            grouped.setdefault(category, []).append(item)
        return grouped

    def add_favorite(self, question, favorite_category=None):
        favorites = self.load_favorites()
        category = str(favorite_category or self.DEFAULT_CATEGORY).strip() or self.DEFAULT_CATEGORY
        key = self._question_key(question)
        if any(
            item.get("question_id") == key
            and (item.get("favorite_category") or self.DEFAULT_CATEGORY) == category
            for item in favorites
        ):
            return favorites, False

        favorites.append({
            "question_id": key,
            "category": question.get("category", "未分類"),
            "favorite_category": category,
            "question_data": question,
        })
        self.favorite_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.favorite_path, "w", encoding="utf-8") as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
        return favorites, True

    def _question_key(self, question):
        return str(question.get("id") or f"{question.get('category', '')}|{question.get('question', '')}")
