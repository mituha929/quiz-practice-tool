# 複題機

複題機是一個以 Python Tkinter 製作的通用題庫複習工具，支援 JSON 題庫匯入、選擇題練習、測驗結果檢討、錯題紀錄與問答題複習。

## 功能特色

- 匯入自訂 JSON 題庫
- 選擇題測驗，支援單選與多選
- 題目與選項可設定亂數排序
- 可在作答時切換上一題與下一題
- 交卷後統一檢查答案
- 結果頁顯示完整選項，選對為綠色、選錯為紅色
- 支援題目解析 `explanation`
- 自動記錄錯題，可進入錯題紀錄模式重新練習
- 可清除或匯出錯題紀錄
- 系統設定支援字體大小、主題模式與結果顯示選項

## 執行方式

需要 Python 3，並使用內建的 Tkinter。

```bash
python question.py
```

如果你的系統使用 `py` 啟動 Python：

```bash
py question.py
```

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

1. 啟動 `question.py`
2. 在首頁點選「匯入題庫 JSON」
3. 選擇符合格式的 `.json` 題庫
4. 匯入成功後即可依分類選題並開始練習

也可以在「系統設定」中查看並複製 JSON 範例。

## 錯題紀錄

交卷後，答錯或未作答的題目會依設定自動加入錯題紀錄。

預設錯題紀錄檔案：

```text
wrong_questions_record.json
```

可在「系統設定」中清除或匯出錯題紀錄。

## 主要檔案

```text
question.py                    主程式
finaltest_question.json         預設選擇題題庫
wlan_qa_review_N_Q.json         預設問答題複習資料
wrong_questions_record.json     錯題紀錄
```

## 專案定位

這個專案原本是課程題庫複習工具，現在已逐步改成通用題庫複習系統。只要題庫符合 JSON 格式，就可以用於不同科目、課程或考試練習。
