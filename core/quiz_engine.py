import random

from core.question_loader import normalize_answer


class QuizEngine:
    def __init__(self, questions):
        self.questions = list(questions)

    def build_question_pool(self, categories=None, start=1, end=None, shuffle_questions=False):
        if categories:
            pool = [q for q in self.questions if q.get("category") in categories]
        else:
            pool = list(self.questions)

        end = end or len(pool)
        selected = pool[start - 1:end]
        if shuffle_questions:
            random.shuffle(selected)
        return selected

    def is_single_choice(self, question):
        return len(normalize_answer(question.get("answer", ""))) == 1

    def build_results(self, selected_questions, saved_answers):
        results = []
        for idx, question in enumerate(selected_questions):
            user_answer = saved_answers.get(idx, [])
            correct_answer = sorted(list(normalize_answer(question.get("answer", ""))))
            results.append({
                "index": idx,
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": user_answer == correct_answer,
            })
        return results

    def calculate_score(self, results):
        return sum(1 for item in results if item["is_correct"])
