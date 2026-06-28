# 複題機

複題機是一個以 Python Tkinter 製作的通用題庫複習工具，支援 JSON 題庫匯入、選擇題練習、測驗結果檢討、錯題紀錄、刷題紀錄、收藏題目、下載本次題目與問答題複習。

## 版本紀錄

| 版本 | 日期 | 修改內容 |
| --- | --- | --- |
| v1.0 | 2026-06-28 | 初版 README 狀態：以 `question.py` 作為主程式，支援 JSON 題庫匯入、選擇題測驗、結果檢討、錯題紀錄、問答題複習與系統設定。 |
| v2.0 | 2026-06-28 | 新增 `main.py` 作為建議入口，並建立 `core/` 與 `gui/` 專案結構。 |
| v2.0 | 2026-06-28 | 將題庫驗證、錯題紀錄、刷題紀錄、收藏題目與題目匯出功能逐步拆到 `core/` 模組。 |
| v2.0 | 2026-06-28 | 新增錯題輸出設定、最近 10 次刷題紀錄、收藏本題、下載本次題目 JSON。 |
| v2.0 | 2026-06-28 | 依 UI/UX 規範統一主內容區按鈕色彩、扁平化按鈕樣式、提示文字對比、Listbox 與輸入框樣式。 |

## 專案結構

```text
quiz-practice-tool/
├── main.py
├── question.py
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── quiz_page.py
│   ├── qa_page.py
│   ├── wrong_page.py
│   └── settings_page.py
├── core/
│   ├── __init__.py
│   ├── question_loader.py
│   ├── wrong_record_manager.py
│   ├── quiz_history_manager.py
│   ├── favorite_manager.py
│   └── export_manager.py
├── README.md
└── .gitignore
```

目前 GUI 主流程仍保留在 `question.py`，`main.py` 是新的建議入口。`core/` 已先承接題庫驗證、錯題紀錄、刷題紀錄、收藏與匯出功能；`gui/` 已建立拆分目標檔案，後續可逐步把頁面程式搬出 `question.py`。

## 安裝與執行

需要 Python 3，並使用內建 Tkinter。

```bash
python main.py
```

仍可使用舊入口：

```bash
python question.py
```

## 功能列表

- 匯入自訂 JSON 題庫
- 選擇題測驗，支援單選與多選
- 題目與選項可設定亂數排序
- 作答時可切換上一題與下一題
- 可收藏目前題目
- 交卷後統一檢查答案
- 結果頁顯示完整選項，選對為綠色、選錯為紅色
- 可顯示或隱藏正確答案與解析
- 自動記錄錯題，可進入錯題紀錄模式重新練習
- 可設定錯題輸出資料夾與檔名
- 可清除或匯出錯題紀錄
- 最近 10 次刷題紀錄
- 可下載本次題目 JSON
- 系統設定支援字體大小與主題模式

## 題庫 JSON 格式

題庫必須是 UTF-8 編碼的 JSON 檔案，最外層必須是 list。每一題至少需要包含：

- `category`：題目分類
- `question`：題目文字，可為字串或字串陣列
- `options`：選項 object
- `answer`：正確答案，可為單選如 `"A"` 或多選如 `"AC"`

建議保留：

- `id`：題號
- `explanation`：解析文字

範例：

```json
[
  {
    "id": "Q001",
    "category": "範例分類",
    "question": "下列哪一個是 Python 的副檔名？",
    "options": {
      "A": ".py",
      "B": ".docx",
      "C": ".jpg",
      "D": ".mp4"
    },
    "answer": "A",
    "explanation": "Python 原始碼檔案通常使用 .py 作為副檔名。"
  },
  {
    "id": "Q002",
    "category": "範例分類",
    "question": [
      "下列哪些屬於程式語言？",
      "請選出所有正確答案。"
    ],
    "options": {
      "A": "Python",
      "B": "HTML",
      "C": "JavaScript",
      "D": "JPEG"
    },
    "answer": "AC",
    "explanation": "Python 與 JavaScript 是程式語言；HTML 是標記語言，JPEG 是圖片格式。"
  }
]
```

## 匯入題庫

1. 啟動程式
2. 在「選擇題測驗」或「系統設定」點選「匯入題庫 JSON」
3. 選擇符合格式的 `.json` 題庫
4. 匯入成功後會更新分類清單並返回選擇題測驗頁

## 錯題輸出

預設錯題輸出路徑：

```text
錯誤題目/錯誤題目題號/wrong_questions_record.json
```

可在「錯題紀錄」頁設定：

- 輸出資料夾
- 輸出檔名
- 匯出錯題紀錄
- 清除錯題紀錄

錯題資料會包含題目、選項、使用者答案、正確答案、解析、錯誤次數與最後錯誤時間。

## 刷題紀錄

每次交卷後會新增一筆紀錄，最多保留最近 10 次。

儲存位置：

```text
user_data/quiz_history/quiz_history.json
```

紀錄包含：

- 測驗日期
- 題庫名稱
- 總題數
- 答對題數
- 錯題題號
- 正確率

## 收藏題目

測驗進行中可點選「收藏本題」。

儲存位置：

```text
user_data/favorites/favorite_questions.json
```

同一題不會重複收藏。

## 下載本次題目

測驗結果頁可點選「下載本次題目 JSON」。

輸出位置：

```text
user_data/exports/
```

檔名格式：

```text
quiz_questions_YYYYMMDD_HHMMSS.json
```

## Git 忽略規則

`.gitignore` 已排除使用者個人資料與本機暫存：

```text
user_data/
錯誤題目/
wrong_questions_record.json
quiz_history.json
favorite_questions.json
__pycache__/
.venv/
dist/
build/
```

預設題庫與範例資料可以放在 GitHub；個人錯題、收藏與刷題紀錄不應 commit。

## TODO

- 將 `question.py` 中的 GUI 頁面逐步移到 `gui/quiz_page.py`、`gui/qa_page.py`、`gui/wrong_page.py`、`gui/settings_page.py`
- 進一步把測驗流程邏輯移到 `core/quiz_engine.py`
- 新增 `data/` 目錄並整理預設題庫位置
- 擴充收藏題目管理頁面
