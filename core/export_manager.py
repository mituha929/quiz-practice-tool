import json
from datetime import datetime
from pathlib import Path


def export_quiz_questions(questions, question_bank_name, output_dir=Path("user_data") / "exports"):
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"quiz_questions_{file_stamp}.json"

    payload = {
        "exported_at": exported_at,
        "question_bank_name": question_bank_name,
        "total_questions": len(questions),
        "questions": questions,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return output_path
