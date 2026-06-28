import json
import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

from core.export_manager import export_quiz_questions
from core.favorite_manager import FavoriteManager
from core.question_loader import (
    import_question_bank,
    index_categories,
    load_json_file,
    validate_choice_question_bank,
)
from core.quiz_engine import QuizEngine
from core.quiz_history_manager import QuizHistoryManager
from core.wrong_record_manager import WrongRecordManager


class QuizGUI:
    def __init__(self, root, file_path, qa_file_path="wlan_qa_review_N_Q.json"):
        self.root = root
        self.app_name = "複題機"
        self.root.title(f"{self.app_name} v1.0")
        self.root.geometry("1080x760")
        self.root.minsize(980, 680)

        # 檔案路徑
        self.file_path = file_path
        self.qa_file_path = qa_file_path

        # 載入選擇題資料
        self.all_questions = self._load_json(file_path, destroy_on_error=True)
        self.categories = self._index_categories()

        # 載入問答題複習資料
        self.qa_questions = self._load_json(qa_file_path, destroy_on_error=False)

        # 選擇題狀態與映射變數
        self.selected_questions = []
        self.current_q_idx = 0
        self.score = 0
        self.user_selections = {}
        self.single_choice_var = tk.StringVar(value="__NONE__")
        self.option_mapping = {}  # 記錄「目前顯示字母」對應到「原始 JSON 字母」
        self.reverse_option_mapping = {}  # 記錄「原始 JSON 字母」對應到「目前顯示字母」
        self.saved_answers = {}
        self.question_option_orders = {}
        self.wrong_manager = WrongRecordManager()
        self.history_manager = QuizHistoryManager()
        self.favorite_manager = FavoriteManager()
        self.wrong_records = self.wrong_manager.load_wrong_records()

        # 問答題複習狀態
        self.qa_selected_questions = []
        self.current_qa_idx = 0

        # GUI 選項變數
        self.shuffle_q_var = tk.BooleanVar(value=False)   # 題目亂數
        self.shuffle_opt_var = tk.BooleanVar(value=True)  # 選項亂數
        self.qa_shuffle_var = tk.BooleanVar(value=False)  # 問答題亂數
        self.font_size_var = tk.StringVar(value="中")
        self.show_explanation_var = tk.BooleanVar(value=True)
        self.show_correct_answer_var = tk.BooleanVar(value=True)
        self.auto_add_wrong_var = tk.BooleanVar(value=True)
        self.theme_var = tk.StringVar(value="淺色")
        self.wrong_output_dir_var = tk.StringVar(value=str(self.wrong_manager.output_dir))
        self.wrong_output_file_var = tk.StringVar(value=self.wrong_manager.file_name)

        self.setup_main_menu()

    def _question_bank_template(self):
        return """[
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
]"""

    def _validate_question_bank(self, data):
        validate_choice_question_bank(data)

    def import_question_bank(self):
        import_path = filedialog.askopenfilename(
            title="匯入題庫 JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not import_path:
            return

        try:
            data = import_question_bank(import_path)
        except Exception as e:
            messagebox.showerror("匯入失敗", f"題庫格式不符合要求：\n{e}")
            return

        self.file_path = import_path
        self.all_questions = data
        self.categories = self._index_categories()
        self._reset_quiz_state(clear_selected=True)
        messagebox.showinfo("匯入成功", f"已匯入 {len(data)} 題：\n{os.path.basename(import_path)}")
        self.show_quiz_home()

    def copy_question_bank_template(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self._question_bank_template())
        messagebox.showinfo("已複製", "JSON 題庫範例已複製到剪貼簿")

    def _load_json(self, file_path, destroy_on_error=False):
        """讀取 JSON 檔案。destroy_on_error=True 時代表主題庫讀不到就結束程式。"""
        try:
            data = load_json_file(file_path)
            if not isinstance(data, list):
                raise ValueError("JSON 最外層必須是 list")
            return data
        except Exception as e:
            if destroy_on_error:
                messagebox.showerror("啟動錯誤", f"無法讀取題庫：{file_path}\n\n錯誤：{e}")
                self.root.destroy()
            else:
                # 問答題檔案讀不到時，不影響原本選擇題功能
                print(f"[提醒] 無法讀取問答題檔案：{file_path}，錯誤：{e}")
            return []

    def _load_wrong_records(self):
        return self.wrong_manager.load_wrong_records()

    def _save_wrong_records(self, wrong_questions):
        self.wrong_records = self.wrong_manager.save_wrong_records(wrong_questions, self.wrong_records)

    def _question_key(self, q):
        return str(q.get("id") or f"{q.get('category', '')}|{q.get('question', '')}")

    def _font(self, size, weight=None):
        scale = {"小": -1, "中": 0, "大": 2}.get(self.font_size_var.get(), 0)
        final_size = max(8, size + scale)
        if weight:
            return ("Microsoft JhengHei UI", final_size, weight)
        return ("Microsoft JhengHei UI", final_size)

    def _theme_colors(self):
        if self.theme_var.get() == "深色":
            return {
                "bg": "#111827",
                "card": "#1F2937",
                "text": "#F9FAFB",
                "muted": "#CBD5E1",
                "sidebar": "#020617",
                "sidebar_text": "#CBD5E1",
                "active": "#2B6CB0",
                "primary": "#2B6CB0",
                "primary_hover": "#245A96",
                "danger": "#E53E3E",
                "danger_hover": "#C53030",
                "border": "#4A5568",
                "secondary_bg": "#1F2937",
            }
        return {
            "bg": "#F4F7FB",
            "card": "white",
            "text": "#2D3748",
            "muted": "#718096",
            "sidebar": "#0F172A",
            "sidebar_text": "#CBD5E1",
            "active": "#2B6CB0",
            "primary": "#2B6CB0",
            "primary_hover": "#245A96",
            "danger": "#E53E3E",
            "danger_hover": "#C53030",
            "border": "#CBD5E0",
            "secondary_bg": "#F7FAFC",
        }

    # Centralized component styling keeps UI colors and button hierarchy consistent.
    def _style_button(self, button, style="primary"):
        colors = self._theme_colors()
        if style == "danger":
            bg = colors["danger"]
            fg = "white"
            active_bg = colors["danger_hover"]
            relief = "flat"
            borderwidth = 0
        elif style == "secondary":
            bg = colors["secondary_bg"]
            fg = colors["text"]
            active_bg = "#E2E8F0" if self.theme_var.get() != "深色" else "#374151"
            relief = "solid"
            borderwidth = 1
        else:
            bg = colors["primary"]
            fg = "white"
            active_bg = colors["primary_hover"]
            relief = "flat"
            borderwidth = 0

        button.configure(
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief=relief,
            bd=borderwidth,
            highlightthickness=0,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        button.bind("<Enter>", lambda event: button.configure(bg=active_bg))
        button.bind("<Leave>", lambda event: button.configure(bg=bg))
        return button

    def _button(self, parent, text, command, style="primary", font_size=11, **kwargs):
        button = tk.Button(
            parent,
            text=text,
            font=self._font(font_size, "bold"),
            command=command,
            **kwargs
        )
        return self._style_button(button, style)

    def _style_listbox(self, listbox):
        colors = self._theme_colors()
        listbox.configure(
            bg=colors["card"],
            fg=colors["text"],
            selectbackground=colors["primary"],
            selectforeground="white",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
            activestyle="none",
            font=self._font(11),
        )
        return listbox

    def _style_entry(self, entry):
        colors = self._theme_colors()
        entry.configure(
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["primary"],
            insertbackground=colors["text"],
        )
        return entry

    def _style_textbox(self, textbox):
        colors = self._theme_colors()
        textbox.configure(
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["primary"],
            padx=10,
            pady=10,
        )
        return textbox

    def clear_wrong_records(self):
        if not self.wrong_records:
            messagebox.showinfo("清除錯題紀錄", "目前沒有錯題紀錄")
            return
        confirm = messagebox.askyesno("清除錯題紀錄", "確定要清除所有錯題紀錄嗎？")
        if not confirm:
            return
        self.wrong_records = []
        self.wrong_manager.clear_wrong_records()
        messagebox.showinfo("清除錯題紀錄", "錯題紀錄已清除")
        self.show_settings_page()

    def export_wrong_records(self):
        if not self.wrong_records:
            messagebox.showinfo("匯出錯題紀錄", "目前沒有錯題可匯出")
            return
        export_path = filedialog.asksaveasfilename(
            title="匯出錯題紀錄",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not export_path:
            return
        output_dir = os.path.dirname(export_path) or "."
        file_name = os.path.basename(export_path)
        self.wrong_manager.export_wrong_records(output_dir, file_name)
        messagebox.showinfo("匯出錯題紀錄", f"已匯出到：\n{export_path}")

    def choose_wrong_output_folder(self):
        folder = filedialog.askdirectory(title="選擇錯題輸出資料夾")
        if folder:
            self.wrong_output_dir_var.set(folder)

    def apply_wrong_output_settings(self):
        self.wrong_manager.set_output_folder(self.wrong_output_dir_var.get())
        self.wrong_manager.set_output_file_name(self.wrong_output_file_var.get())
        self.wrong_output_file_var.set(self.wrong_manager.file_name)
        self.wrong_records = self.wrong_manager.load_wrong_records()
        messagebox.showinfo("錯題輸出設定", f"已套用：\n{self.wrong_manager.get_output_path()}")
        self.show_wrong_home()

    def _index_categories(self):
        return index_categories(self.all_questions)

    def _reset_quiz_state(self, clear_selected=False):
        if clear_selected:
            self.selected_questions = []
        self.current_q_idx = 0
        self.score = 0
        self.user_selections = {}
        self.single_choice_var.set("__NONE__")
        self.option_mapping = {}
        self.reverse_option_mapping = {}
        self.saved_answers = {}
        self.question_option_orders = {}

    def setup_main_menu(self):
        self.show_quiz_home()

    def setup_layout(self, active_page="quiz"):
        self.clear_frame()
        colors = self._theme_colors()

        self.app_frame = tk.Frame(self.root, bg=colors["bg"])
        self.app_frame.pack(expand=True, fill="both")

        self.sidebar = tk.Frame(self.app_frame, bg=colors["sidebar"], width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_area = tk.Frame(self.app_frame, bg=colors["bg"])
        self.main_area.pack(side="left", expand=True, fill="both")

        self._build_sidebar(active_page)

    def _build_sidebar(self, active_page):
        colors = self._theme_colors()
        title = tk.Label(
            self.sidebar,
            text=f"{self.app_name}\nQuiz Review",
            font=("Microsoft JhengHei UI", 18, "bold"),
            fg="white",
            bg=colors["sidebar"],
            justify="left"
        )
        title.pack(anchor="w", padx=22, pady=(28, 24))

        menu_items = [
            ("quiz", "📘  選擇題測驗", self.show_quiz_home),
            ("wrong", "❌  錯題紀錄", self.show_wrong_home),
            ("qa", "💬  問答題複習", self.show_qa_home),
            ("settings", "⚙️  系統設定", self.show_settings_page),
            ("about", "ℹ️  關於說明", self.show_about_page),
        ]

        for page_key, text, command in menu_items:
            is_active = page_key == active_page
            bg = colors["active"] if is_active else colors["sidebar"]
            fg = "white" if is_active else "#CBD5E1"

            btn = tk.Button(
                self.sidebar,
                text=text,
                font=("Microsoft JhengHei UI", 11, "bold"),
                bg=bg,
                fg=fg,
                activebackground="#1D4ED8",
                activeforeground="white",
                relief="flat",
                anchor="w",
                padx=18,
                pady=12,
                command=command
            )
            btn.pack(fill="x", padx=14, pady=4)

        footer = tk.Label(
            self.sidebar,
            text="v1.0\n通用題庫複習",
            font=("Microsoft JhengHei UI", 9),
            fg="#94A3B8",
            bg=colors["sidebar"],
            justify="left"
        )
        footer.pack(side="bottom", anchor="w", padx=22, pady=24)

    def show_quiz_home(self):
        self.setup_layout(active_page="quiz")
        colors = self._theme_colors()

        container = tk.Frame(self.main_area, bg=colors["bg"], padx=28, pady=24)
        container.pack(expand=True, fill="both")

        tk.Label(
            container,
            text="選擇題測驗",
            font=self._font(24, "bold"),
            fg=colors["text"],
            bg=colors["bg"]
        ).pack(anchor="w")

        header_actions = tk.Frame(container, bg=colors["bg"])
        header_actions.pack(fill="x", pady=(0, 10))

        self._button(
            header_actions,
            text="匯入題庫 JSON",
            command=self.import_question_bank,
            height=2
        ).pack(side="left")

        tk.Label(
            header_actions,
            text=f"目前題庫：{os.path.basename(self.file_path)}",
            font=self._font(10),
            fg=colors["muted"],
            bg=colors["bg"]
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            container,
            text="選擇要練習的大題、設定出題方式，並開始測驗。",
            font=self._font(11),
            fg=colors["muted"],
            bg=colors["bg"]
        ).pack(anchor="w", pady=(4, 18))

        card = tk.Frame(container, bg=colors["card"], padx=22, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text="1. 選擇大題（按住 Ctrl 可多選）",
            font=self._font(13, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w")

        sorted_cats = sorted(self.categories.keys(), key=lambda x: x.replace(" ", "-"))

        self.listbox = tk.Listbox(
            card,
            selectmode=tk.MULTIPLE,
            height=10,
            exportselection=False,
        )
        self._style_listbox(self.listbox)
        self.listbox.insert(tk.END, "0. [全題庫] 包含所有章節題目")
        for cat in sorted_cats:
            self.listbox.insert(tk.END, f"{cat} (共 {len(self.categories[cat])} 題)")
        self.listbox.pack(fill="x", pady=(8, 8))
        self.listbox.bind("<<ListboxSelect>>", lambda event: self.update_pool_info(sorted_cats))

        self.pool_info_label = tk.Label(
            card,
            text=f"目前題目池：尚未選擇（全題庫共 {len(self.all_questions)} 題）",
            fg=colors["muted"],
            bg=colors["card"],
            font=self._font(10)
        )
        self.pool_info_label.pack(anchor="w", pady=(0, 14))

        tk.Label(
            card,
            text="2. 出題與顯示設定",
            font=self._font(13, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(6, 4))

        tk.Checkbutton(
            card,
            text="開啟「題目」亂數排序",
            variable=self.shuffle_q_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w")

        tk.Checkbutton(
            card,
            text="開啟「選項」亂數排序（防止死背位置）",
            variable=self.shuffle_opt_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w")

        tk.Label(
            card,
            text="3. 選擇範圍（選定題目池編號）",
            font=self._font(13, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(14, 4))

        range_frame = tk.Frame(card, bg=colors["card"])
        range_frame.pack(anchor="w", pady=(4, 14))

        self.start_entry = tk.Entry(range_frame, width=6, justify="center", font=self._font(11))
        self._style_entry(self.start_entry)
        self.start_entry.insert(0, "1")
        self.start_entry.pack(side="left")

        tk.Label(range_frame, text=" 到 ", bg=colors["card"], fg=colors["text"], font=self._font(11)).pack(side="left")

        self.end_entry = tk.Entry(range_frame, width=6, justify="center", font=self._font(11))
        self._style_entry(self.end_entry)
        self.end_entry.insert(0, "10")
        self.end_entry.pack(side="left")

        self._button(
            card,
            text="確認並開始測驗",
            command=lambda: self.prepare_quiz(sorted_cats),
            font_size=13,
            height=2
        ).pack(fill="x", pady=(12, 0))

        history = self.history_manager.load_history()
        if history:
            tk.Label(
                card,
                text="最近刷題紀錄",
                font=self._font(13, "bold"),
                fg=colors["text"],
                bg=colors["card"]
            ).pack(anchor="w", pady=(18, 6))
            for record in history[:10]:
                text = (
                    f"{record.get('quiz_date', '')} | {record.get('question_bank_name', '')} | "
                    f"{record.get('correct_count', 0)}/{record.get('total_questions', 0)} | "
                    f"{record.get('accuracy', 0):.1f}%"
                )
                tk.Label(
                    card,
                    text=text,
                    font=self._font(10),
                    fg=colors["muted"],
                    bg=colors["card"],
                    anchor="w"
                ).pack(fill="x", pady=1)

    def show_wrong_home(self):
        self.setup_layout(active_page="wrong")
        colors = self._theme_colors()

        container = tk.Frame(self.main_area, bg=colors["bg"], padx=28, pady=24)
        container.pack(expand=True, fill="both")

        wrong_count = len(self.wrong_records)

        tk.Label(
            container,
            text="錯題紀錄",
            font=self._font(24, "bold"),
            fg=colors["text"],
            bg=colors["bg"]
        ).pack(anchor="w")

        tk.Label(
            container,
            text=f"目前共有 {wrong_count} 題錯題，可針對錯題重新練習。",
            font=self._font(11),
            fg=colors["muted"],
            bg=colors["bg"]
        ).pack(anchor="w", pady=(4, 18))

        card = tk.Frame(container, bg=colors["card"], padx=22, pady=20)
        card.pack(fill="x")

        tk.Label(
            card,
            text=f"目前錯題數：{wrong_count} 題",
            font=self._font(16, "bold"),
            fg="#B91C1C",
            bg=colors["card"]
        ).pack(anchor="w", pady=(0, 12))

        self._button(
            card,
            text="開始錯題紀錄模式",
            command=self.start_wrong_record_quiz,
            font_size=13,
            height=2,
            state=tk.NORMAL if wrong_count else tk.DISABLED
        ).pack(fill="x")

        settings_card = tk.Frame(container, bg=colors["card"], padx=22, pady=20)
        settings_card.pack(fill="x", pady=(16, 0))

        tk.Label(
            settings_card,
            text="錯題輸出設定",
            font=self._font(14, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(0, 8))

        folder_frame = tk.Frame(settings_card, bg=colors["card"])
        folder_frame.pack(fill="x", pady=4)
        tk.Label(folder_frame, text="輸出資料夾", font=self._font(10, "bold"), fg=colors["text"], bg=colors["card"]).pack(anchor="w")
        folder_input_frame = tk.Frame(folder_frame, bg=colors["card"])
        folder_input_frame.pack(fill="x", pady=(2, 0))
        folder_entry = tk.Entry(folder_input_frame, textvariable=self.wrong_output_dir_var, font=self._font(10))
        self._style_entry(folder_entry)
        folder_entry.pack(side="left", fill="x", expand=True)
        self._button(folder_input_frame, text="選擇資料夾", font_size=10, command=self.choose_wrong_output_folder, style="secondary").pack(side="left", padx=(8, 0))

        file_frame = tk.Frame(settings_card, bg=colors["card"])
        file_frame.pack(fill="x", pady=4)
        tk.Label(file_frame, text="輸出檔名", font=self._font(10, "bold"), fg=colors["text"], bg=colors["card"]).pack(anchor="w")
        file_entry = tk.Entry(file_frame, textvariable=self.wrong_output_file_var, font=self._font(10))
        self._style_entry(file_entry)
        file_entry.pack(fill="x", pady=(2, 0))

        tk.Label(
            settings_card,
            text=f"目前輸出路徑：{self.wrong_manager.get_output_path()}",
            font=self._font(10),
            fg=colors["muted"],
            bg=colors["card"],
            wraplength=760,
            justify="left"
        ).pack(anchor="w", pady=(6, 8))

        action_frame = tk.Frame(settings_card, bg=colors["card"])
        action_frame.pack(fill="x")
        self._button(action_frame, text="套用設定", font_size=10, command=self.apply_wrong_output_settings, style="secondary").pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._button(action_frame, text="匯出錯題紀錄", font_size=10, command=self.export_wrong_records, style="secondary", state=tk.NORMAL if wrong_count else tk.DISABLED).pack(side="left", fill="x", expand=True, padx=4)
        self._button(action_frame, text="清除錯題紀錄", font_size=10, command=self.clear_wrong_records, style="danger", state=tk.NORMAL if wrong_count else tk.DISABLED).pack(side="left", fill="x", expand=True, padx=(4, 0))

    def show_qa_home(self):
        self.setup_layout(active_page="qa")
        colors = self._theme_colors()

        container = tk.Frame(self.main_area, bg=colors["bg"], padx=28, pady=24)
        container.pack(expand=True, fill="both")

        tk.Label(
            container,
            text="問答題複習",
            font=self._font(24, "bold"),
            fg=colors["text"],
            bg=colors["bg"]
        ).pack(anchor="w")

        tk.Label(
            container,
            text="適合用來背誦英文題目、中文翻譯、答案與考試重點。",
            font=self._font(11),
            fg=colors["muted"],
            bg=colors["bg"]
        ).pack(anchor="w", pady=(4, 18))

        card = tk.Frame(container, bg=colors["card"], padx=22, pady=20)
        card.pack(fill="x")

        qa_count = len(self.qa_questions)
        qa_file_name = os.path.basename(self.qa_file_path)

        tk.Label(
            card,
            text=f"複習來源：{qa_file_name}",
            font=self._font(12, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w")

        tk.Label(
            card,
            text=f"共 {qa_count} 題，可用於問答題或重點複習",
            font=self._font(10),
            fg=colors["muted"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(4, 12))

        tk.Checkbutton(
            card,
            text="開啟「問答題」亂數排序",
            variable=self.qa_shuffle_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w", pady=(0, 12))

        self._button(
            card,
            text="開始複習問答題",
            command=self.start_qa_review,
            font_size=13,
            height=2
        ).pack(fill="x")

    def show_settings_page(self):
        self.setup_layout(active_page="settings")
        colors = self._theme_colors()

        container = tk.Frame(self.main_area, bg=colors["bg"], padx=28, pady=24)
        container.pack(expand=True, fill="both")

        tk.Label(
            container,
            text="系統設定",
            font=self._font(24, "bold"),
            fg=colors["text"],
            bg=colors["bg"]
        ).pack(anchor="w")

        tk.Label(
            container,
            text="調整測驗顯示、結果頁內容、錯題紀錄與預設出題方式。",
            font=self._font(11),
            fg=colors["muted"],
            bg=colors["bg"]
        ).pack(anchor="w", pady=(4, 18))

        canvas = tk.Canvas(container, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        settings_content = tk.Frame(canvas, bg=colors["bg"])
        settings_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window = canvas.create_window((0, 0), window=settings_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        card = tk.Frame(settings_content, bg=colors["card"], padx=22, pady=20)
        card.pack(fill="x")

        tk.Label(
            card,
            text="顯示設定",
            font=self._font(14, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(0, 10))

        font_frame = tk.Frame(card, bg=colors["card"])
        font_frame.pack(anchor="w", fill="x", pady=(0, 8))
        tk.Label(font_frame, text="字體大小：", font=self._font(11, "bold"), fg=colors["text"], bg=colors["card"]).pack(side="left")
        for label in ["小", "中", "大"]:
            tk.Radiobutton(
                font_frame,
                text=label,
                variable=self.font_size_var,
                value=label,
                bg=colors["card"],
                fg=colors["text"],
                selectcolor=colors["card"],
                font=self._font(10),
                command=self.show_settings_page
            ).pack(side="left", padx=(4, 10))

        theme_frame = tk.Frame(card, bg=colors["card"])
        theme_frame.pack(anchor="w", fill="x", pady=(0, 12))
        tk.Label(theme_frame, text="主題模式：", font=self._font(11, "bold"), fg=colors["text"], bg=colors["card"]).pack(side="left")
        for label in ["淺色", "深色"]:
            tk.Radiobutton(
                theme_frame,
                text=label,
                variable=self.theme_var,
                value=label,
                bg=colors["card"],
                fg=colors["text"],
                selectcolor=colors["card"],
                font=self._font(10),
                command=self.show_settings_page
            ).pack(side="left", padx=(4, 10))

        tk.Checkbutton(
            card,
            text="測驗結果中顯示解析",
            variable=self.show_explanation_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            card,
            text="測驗結果中顯示正確答案",
            variable=self.show_correct_answer_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            card,
            text="交卷後自動加入錯題紀錄",
            variable=self.auto_add_wrong_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w", pady=2)

        tk.Label(
            card,
            text="預設出題方式",
            font=self._font(14, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(18, 8))

        tk.Checkbutton(
            card,
            text="題目預設亂數",
            variable=self.shuffle_q_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            card,
            text="選項預設亂數",
            variable=self.shuffle_opt_var,
            bg=colors["card"],
            fg=colors["text"],
            selectcolor=colors["card"],
            font=self._font(10)
        ).pack(anchor="w", pady=2)

        tk.Label(
            card,
            text="錯題紀錄管理",
            font=self._font(14, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(18, 8))

        wrong_count = len(self.wrong_records)
        tk.Label(
            card,
            text=f"目前錯題數：{wrong_count} 題",
            font=self._font(10),
            fg=colors["muted"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(0, 8))

        action_frame = tk.Frame(card, bg=colors["card"])
        action_frame.pack(fill="x")

        self._button(
            action_frame,
            text="清除錯題紀錄",
            command=self.clear_wrong_records,
            style="danger",
            height=2,
            state=tk.NORMAL if wrong_count else tk.DISABLED
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._button(
            action_frame,
            text="匯出錯題紀錄",
            command=self.export_wrong_records,
            style="secondary",
            height=2,
            state=tk.NORMAL if wrong_count else tk.DISABLED
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        import_card = tk.Frame(settings_content, bg=colors["card"], padx=22, pady=20)
        import_card.pack(fill="x", pady=(16, 0))

        tk.Label(
            import_card,
            text="題庫匯入與 JSON 格式",
            font=self._font(14, "bold"),
            fg=colors["text"],
            bg=colors["card"]
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            import_card,
            text="選擇題題庫必須是 UTF-8 JSON。必要欄位：category、question、options、answer；explanation 與 id 可選但建議保留。",
            font=self._font(10),
            fg=colors["muted"],
            bg=colors["card"],
            wraplength=760,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        import_action_frame = tk.Frame(import_card, bg=colors["card"])
        import_action_frame.pack(fill="x", pady=(0, 10))

        self._button(
            import_action_frame,
            text="匯入題庫 JSON",
            command=self.import_question_bank,
            height=2
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._button(
            import_action_frame,
            text="複製 JSON 範例",
            command=self.copy_question_bank_template,
            style="secondary",
            height=2
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        template_text = tk.Text(
            import_card,
            height=18,
            wrap="none",
            font=("Consolas", 10),
            bg="#0F172A",
            fg="#E5E7EB",
            insertbackground="#E5E7EB",
            relief="flat"
        )
        self._style_textbox(template_text)
        template_text.insert("1.0", self._question_bank_template())
        template_text.configure(state="disabled")
        template_text.pack(fill="both", expand=True)

    def show_about_page(self):
        self.setup_layout(active_page="about")
        colors = self._theme_colors()

        container = tk.Frame(self.main_area, bg=colors["bg"], padx=28, pady=24)
        container.pack(expand=True, fill="both")

        tk.Label(
            container,
            text="關於說明",
            font=self._font(24, "bold"),
            fg=colors["text"],
            bg=colors["bg"]
        ).pack(anchor="w")

        card = tk.Frame(container, bg=colors["card"], padx=22, pady=20)
        card.pack(fill="x", pady=(18, 0))

        about_text = (
            "本系統可用於各類課程、考試與自學題庫複習，包含選擇題測驗、錯題紀錄與問答題複習。\n\n"
            "選擇題題庫使用 JSON 格式，可在系統設定中查看格式範例並匯入自己的題庫。"
        )

        tk.Label(
            card,
            text=about_text,
            font=self._font(12),
            fg=colors["text"],
            bg=colors["card"],
            justify="left",
            wraplength=720
        ).pack(anchor="w")

    def update_pool_info(self, sorted_cats):
        indices = self.listbox.curselection()
        if not indices:
            text = f"目前題目池：尚未選擇（全題庫共 {len(self.all_questions)} 題）"
        elif 0 in indices:
            text = f"目前題目池：全題庫，共 {len(self.all_questions)} 題，可輸入範圍 1 到 {len(self.all_questions)}"
        else:
            total = sum(len(self.categories[sorted_cats[i - 1]]) for i in indices)
            text = f"目前題目池：已選 {len(indices)} 個大題，共 {total} 題，可輸入範圍 1 到 {total}"
        self.pool_info_label.config(text=text)

    # =========================
    # 選擇題測驗功能：保留原本邏輯
    # =========================
    def prepare_quiz(self, sorted_cats):
        indices = self.listbox.curselection()
        if not indices:
            messagebox.showwarning("提示", "請至少選擇一個大題")
            return

        if 0 in indices:
            pool = list(self.all_questions)
        else:
            chosen_categories = [sorted_cats[i - 1] for i in indices]
            pool = [q for q in self.all_questions if q.get("category") in chosen_categories]

        try:
            start = int(self.start_entry.get()) if self.start_entry.get() else 1
            end = int(self.end_entry.get()) if self.end_entry.get() else len(pool)

            if start < 1 or end < start:
                raise ValueError("起始與結束範圍不正確")
            if end > len(pool):
                raise ValueError(f"結束範圍不可超過目前題目池總數 {len(pool)}")

            self.selected_questions = pool[start - 1:end]
            if not self.selected_questions:
                messagebox.showwarning("提示", "此範圍內沒有題目")
                return

            if self.shuffle_q_var.get():
                random.shuffle(self.selected_questions)

            self._reset_quiz_state()
            self.show_question_ui()
        except Exception as e:
            messagebox.showerror("錯誤", f"範圍設定無效：{e}")

    def start_wrong_record_quiz(self):
        if not self.wrong_records:
            messagebox.showinfo("錯題紀錄", "目前沒有錯題紀錄")
            return

        self.selected_questions = [
            record.get("question_data", record)
            for record in self.wrong_records
            if isinstance(record.get("question_data", record), dict)
        ]
        if not self.selected_questions:
            messagebox.showinfo("錯題紀錄", "目前沒有可練習的錯題")
            return

        self._reset_quiz_state()
        self.show_question_ui()

    def show_question_ui(self):
        self.clear_frame()
        self.quiz_frame = tk.Frame(self.root, padx=30, pady=20)
        self.quiz_frame.pack(expand=True, fill="both")

        nav_content_frame = tk.Frame(self.quiz_frame)
        nav_content_frame.pack(expand=True, fill="both")

        self.prev_button = tk.Button(
            nav_content_frame,
            text="←",
            font=self._font(18, "bold"),
            width=3,
            command=self.prev_quiz_question
        )
        self._style_button(self.prev_button, "secondary")
        self.prev_button.pack(side="left", fill="y", padx=(0, 8))

        content_frame = tk.Frame(nav_content_frame)
        content_frame.pack(side="left", expand=True, fill="both")

        self.quiz_canvas = tk.Canvas(content_frame, highlightthickness=0)
        quiz_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.quiz_canvas.yview)
        self.quiz_content = tk.Frame(self.quiz_canvas)

        self.quiz_content.bind(
            "<Configure>",
            lambda e: self.quiz_canvas.configure(scrollregion=self.quiz_canvas.bbox("all"))
        )
        self.quiz_window = self.quiz_canvas.create_window((0, 0), window=self.quiz_content, anchor="nw")
        self.quiz_canvas.configure(yscrollcommand=quiz_scrollbar.set)
        self.quiz_canvas.bind(
            "<Configure>",
            lambda e: self.quiz_canvas.itemconfigure(self.quiz_window, width=e.width)
        )

        self.quiz_canvas.pack(side="left", fill="both", expand=True)
        quiz_scrollbar.pack(side="right", fill="y")
        self.quiz_canvas.bind("<Enter>", lambda event: self.quiz_canvas.bind_all("<MouseWheel>", self._on_quiz_mousewheel))
        self.quiz_canvas.bind("<Leave>", lambda event: self.quiz_canvas.unbind_all("<MouseWheel>"))

        self.next_button = tk.Button(
            nav_content_frame,
            text="→",
            font=self._font(18, "bold"),
            width=3,
            command=self.next_quiz_question
        )
        self._style_button(self.next_button, "secondary")
        self.next_button.pack(side="left", fill="y", padx=(8, 0))

        self.q_text = tk.Label(
            self.quiz_content,
            text="",
            wraplength=700,
            justify="left",
            font=self._font(12, "bold")
        )
        self.q_text.pack(pady=20, anchor="w")

        self.options_container = tk.Frame(self.quiz_content)
        self.options_container.pack(fill="x", pady=10)

        # 測驗模式按鈕列：先暫存答案，最後統一交卷
        quiz_btn_frame = tk.Frame(self.quiz_frame)
        quiz_btn_frame.pack(fill="x", side="bottom", pady=20)

        self._button(
            quiz_btn_frame,
            text="儲存本題答案",
            command=self.save_current_answer,
            height=2
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        self._button(
            quiz_btn_frame,
            text="收藏本題",
            command=self.add_current_question_to_favorites,
            style="secondary",
            height=2
        ).pack(side="left", fill="x", expand=True, padx=5)

        self._button(
            quiz_btn_frame,
            text="交卷並查看結果",
            command=self.submit_quiz,
            height=2
        ).pack(side="left", fill="x", expand=True, padx=5)

        self._button(
            quiz_btn_frame,
            text="結束測驗 / 返回主選單",
            command=self.exit_quiz_to_menu,
            style="secondary",
            height=2
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.progress_bar = ttk.Progressbar(self.quiz_frame, mode="determinate")
        self.progress_bar.pack(fill="x", side="bottom", pady=5)
        self.info_label = tk.Label(self.quiz_frame, text="", fg="#757575")
        self.info_label.pack(side="bottom")

        self.load_next_question()

    def _on_quiz_mousewheel(self, event):
        try:
            self.quiz_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def load_next_question(self):
        if self.current_q_idx < len(self.selected_questions):
            q = self.selected_questions[self.current_q_idx]
            txt = q.get("question", "")
            if isinstance(txt, list):
                txt = "\n".join(txt)
            self.q_text.config(text=f"Q{self.current_q_idx + 1}: {txt}")

            for widget in self.options_container.winfo_children():
                widget.destroy()

            options = q.get("options", {})
            if not options:
                tk.Label(
                    self.options_container,
                    text="此題沒有 options 欄位，請改用問答題複習模式或檢查 JSON。",
                    fg="red",
                    font=("Arial", 11, "bold")
                ).pack(anchor="w")
                return

            # --- 選項亂數核心邏輯：每題只建立一次，避免上一題/下一題時選項跳動 ---
            if self.current_q_idx not in self.question_option_orders:
                orig_options = list(options.items())
                if self.shuffle_opt_var.get():
                    random.shuffle(orig_options)
                self.question_option_orders[self.current_q_idx] = orig_options
            else:
                orig_options = self.question_option_orders[self.current_q_idx]

            self.user_selections = {}
            self.single_choice_var.set("__NONE__")
            self.option_mapping = {}
            self.reverse_option_mapping = {}
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            is_single_choice = len(self._normalize_answer(q.get("answer", ""))) == 1
            saved_original = set(self.saved_answers.get(self.current_q_idx, []))

            for i, (orig_key, content) in enumerate(orig_options):
                display_key = letters[i]
                normalized_orig_key = str(orig_key).upper()
                self.option_mapping[display_key] = normalized_orig_key
                self.reverse_option_mapping[normalized_orig_key] = display_key

                if is_single_choice:
                    if normalized_orig_key in saved_original:
                        self.single_choice_var.set(display_key)
                    tk.Radiobutton(
                        self.options_container,
                        text=f"({display_key}) {content}",
                        variable=self.single_choice_var,
                        value=display_key,
                        tristatevalue="__TRISTATE__",
                        font=self._font(11),
                        anchor="w",
                        wraplength=680,
                        justify="left"
                    ).pack(fill="x", pady=4)
                else:
                    var = tk.BooleanVar(value=normalized_orig_key in saved_original)
                    self.user_selections[display_key] = var
                    tk.Checkbutton(
                        self.options_container,
                        text=f"({display_key}) {content}",
                        variable=var,
                        font=self._font(11),
                        anchor="w",
                        wraplength=680,
                        justify="left"
                    ).pack(fill="x", pady=4)

            answered = len(self.saved_answers)
            self.info_label.config(text=f"進度：{self.current_q_idx + 1} / {len(self.selected_questions)}，已儲存：{answered} / {len(self.selected_questions)}")
            self.progress_bar["value"] = (self.current_q_idx / len(self.selected_questions)) * 100
            self.prev_button.config(state=tk.NORMAL if self.current_q_idx > 0 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if self.current_q_idx < len(self.selected_questions) - 1 else tk.DISABLED)
        else:
            self.final_result()

    def _normalize_answer(self, answer):
        return str(answer).replace(" ", "").replace(",", "").upper()

    def _get_selected_display_answers(self):
        if self.single_choice_var.get() and self.single_choice_var.get() != "__NONE__":
            return [self.single_choice_var.get()]
        return [k for k, v in self.user_selections.items() if v.get()]

    def _format_correct_answer_for_current_display(self, correct_ans, options):
        display_letters = []
        details = []
        normalized_options = {str(key).upper(): value for key, value in options.items()}
        for orig_key in sorted(correct_ans):
            display_key = self.reverse_option_mapping.get(orig_key, orig_key)
            display_letters.append(display_key)
            if orig_key in normalized_options:
                details.append(f"({display_key}) {normalized_options[orig_key]}")
        if details:
            return f"{''.join(sorted(display_letters))}\n\n" + "\n".join(details)
        return "".join(sorted(display_letters))

    def save_current_answer(self, show_message=True):
        selected_display = self._get_selected_display_answers()
        if not selected_display:
            self.saved_answers.pop(self.current_q_idx, None)
            if show_message:
                messagebox.showinfo("儲存答案", "本題目前未選擇答案，已清除暫存答案")
            self._refresh_quiz_info()
            return False

        selected_original = [self.option_mapping[k] for k in selected_display]
        selected_original.sort()
        self.saved_answers[self.current_q_idx] = selected_original
        if show_message:
            messagebox.showinfo("儲存答案", "本題答案已儲存")
        self._refresh_quiz_info()
        return True

    def _refresh_quiz_info(self):
        if hasattr(self, "info_label"):
            answered = len(self.saved_answers)
            self.info_label.config(text=f"進度：{self.current_q_idx + 1} / {len(self.selected_questions)}，已儲存：{answered} / {len(self.selected_questions)}")

    def prev_quiz_question(self):
        self.save_current_answer(show_message=False)
        if self.current_q_idx > 0:
            self.current_q_idx -= 1
            self.load_next_question()

    def next_quiz_question(self):
        self.save_current_answer(show_message=False)
        if self.current_q_idx < len(self.selected_questions) - 1:
            self.current_q_idx += 1
            self.load_next_question()

    def add_current_question_to_favorites(self):
        if not self.selected_questions:
            return
        question = self.selected_questions[self.current_q_idx]
        _, added = self.favorite_manager.add_favorite(question)
        if added:
            messagebox.showinfo("收藏題目", "已收藏本題")
        else:
            messagebox.showinfo("收藏題目", "本題已在收藏清單中")

    def export_current_quiz_questions(self):
        if not self.selected_questions:
            messagebox.showinfo("下載本次題目", "目前沒有可下載的題目")
            return
        output_path = export_quiz_questions(self.selected_questions, os.path.basename(self.file_path))
        messagebox.showinfo("下載本次題目", f"已匯出：\n{output_path}")

    def submit_quiz(self):
        self.save_current_answer(show_message=False)
        unanswered = len(self.selected_questions) - len(self.saved_answers)
        if unanswered:
            confirm = messagebox.askyesno(
                "交卷確認",
                f"目前還有 {unanswered} 題未儲存答案，確定要交卷嗎？"
            )
            if not confirm:
                return
        else:
            confirm = messagebox.askyesno("交卷確認", "確定要交卷並查看結果嗎？")
            if not confirm:
                return

        results = self._build_quiz_results()
        self.score = QuizEngine(self.selected_questions).calculate_score(results)
        wrong_questions = [item for item in results if not item["is_correct"]]
        if self.auto_add_wrong_var.get():
            self._save_wrong_records(wrong_questions)
        self._save_quiz_history(results, wrong_questions)
        self.show_quiz_results(results)

    def _save_quiz_history(self, results, wrong_questions):
        total = len(results)
        correct_count = sum(1 for item in results if item["is_correct"])
        accuracy = (correct_count / total) * 100 if total else 0
        wrong_question_ids = [
            str(item["question"].get("id") or self._question_key(item["question"]))
            for item in wrong_questions
        ]
        self.history_manager.add_history({
            "quiz_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question_bank_name": os.path.basename(self.file_path),
            "total_questions": total,
            "correct_count": correct_count,
            "wrong_question_ids": wrong_question_ids,
            "accuracy": accuracy,
        })

    def _build_quiz_results(self):
        return QuizEngine(self.selected_questions).build_results(self.selected_questions, self.saved_answers)

    def _add_result_options(self, parent, q, user_answer, correct_answer):
        options = q.get("options", {})
        if not options:
            tk.Label(
                parent,
                text="此題沒有 options 欄位",
                font=self._font(10),
                fg="#B71C1C",
                anchor="w"
            ).pack(fill="x", pady=(4, 0))
            return

        user_set = set(user_answer)
        correct_set = set(correct_answer)

        tk.Label(
            parent,
            text="全部選項：",
            font=self._font(10, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(6, 2))

        for key, content in options.items():
            normalized_key = str(key).upper()
            is_correct = normalized_key in correct_set
            is_selected = normalized_key in user_set
            is_wrong_selected = is_selected and not is_correct
            can_show_correct = self.show_correct_answer_var.get()

            if is_wrong_selected:
                bg = "#FFCDD2"
                fg = "#B71C1C"
                prefix = "你選錯"
            elif is_selected and is_correct:
                bg = "#C8E6C9"
                fg = "#1B5E20"
                prefix = "你選對"
            elif is_correct and can_show_correct:
                bg = "#C8E6C9"
                fg = "#1B5E20"
                prefix = "正確答案"
            elif is_selected:
                bg = "#E0F2FE"
                fg = "#075985"
                prefix = "你選擇"
            else:
                bg = "white"
                fg = "#212121"
                prefix = ""

            option_frame = tk.Frame(parent, bg=bg, padx=8, pady=6)
            option_frame.pack(fill="x", pady=2)

            label_text = f"({normalized_key}) {content}"
            if prefix:
                label_text = f"[{prefix}] {label_text}"

            tk.Label(
                option_frame,
                text=label_text,
                font=self._font(10),
                fg=fg,
                bg=bg,
                wraplength=700,
                justify="left",
                anchor="w"
            ).pack(fill="x")

    def show_quiz_results(self, results):
        self.clear_frame()
        result_frame = tk.Frame(self.root, padx=25, pady=18)
        result_frame.pack(expand=True, fill="both")

        total = len(results)
        wrong_count = total - self.score
        tk.Label(
            result_frame,
            text=f"測驗結果：{self.score} / {total}，錯題 {wrong_count} 題",
            font=self._font(15, "bold"),
            fg="#1A237E"
        ).pack(anchor="w", pady=(0, 8))

        content_frame = tk.Frame(result_frame)
        content_frame.pack(expand=True, fill="both")

        canvas = tk.Canvas(content_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas)
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))

        for item in results:
            q = item["question"]
            idx = item["index"]
            question_text = q.get("question", "")
            if isinstance(question_text, list):
                question_text = "\n".join(question_text)

            block = tk.Frame(content, bd=1, relief="solid", padx=10, pady=8)
            block.pack(fill="x", pady=6)

            status_text = "答對" if item["is_correct"] else "答錯"
            status_color = "#1B5E20" if item["is_correct"] else "#B71C1C"
            tk.Label(
                block,
                text=f"Q{idx + 1}：{status_text}",
                font=self._font(12, "bold"),
                fg=status_color,
                anchor="w"
            ).pack(fill="x")
            tk.Label(block, text=question_text, font=self._font(11, "bold"), wraplength=700, justify="left", anchor="w").pack(fill="x", pady=(4, 6))
            self._add_result_options(block, q, item["user_answer"], item["correct_answer"])
            if self.show_explanation_var.get():
                tk.Label(block, text="題目解析：", font=self._font(10, "bold"), fg="#0D47A1", anchor="w").pack(fill="x", pady=(6, 0))
                tk.Label(block, text=q.get("explanation", "無"), font=self._font(10), wraplength=700, justify="left", anchor="w").pack(fill="x")

        btn_frame = tk.Frame(result_frame)
        btn_frame.pack(fill="x", pady=(12, 0))
        self._button(
            btn_frame,
            text="返回主選單",
            command=self.setup_main_menu,
            style="secondary",
            height=2
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._button(
            btn_frame,
            text="下載本次題目 JSON",
            command=self.export_current_quiz_questions,
            height=2
        ).pack(side="left", fill="x", expand=True, padx=5)
        self._button(
            btn_frame,
            text="進入錯題紀錄模式",
            command=self.start_wrong_record_quiz,
            height=2,
            state=tk.NORMAL if self.wrong_records else tk.DISABLED
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def exit_quiz_to_menu(self):
        """讓選擇題測驗可以像問答題複習一樣，隨時返回主選單。"""
        total = len(self.selected_questions)
        answered = self.current_q_idx

        confirm = messagebox.askyesno(
            "結束測驗",
            f"確定要結束目前測驗並返回主選單嗎？\n\n"
            f"目前進度：{answered} / {total}\n"
            f"目前得分：{self.score} / {answered if answered > 0 else 0}"
        )

        if confirm:
            self._reset_quiz_state(clear_selected=True)
            self.setup_main_menu()

    def final_result(self):
        total = len(self.selected_questions)
        if total == 0:
            messagebox.showinfo("測驗結束", "沒有題目可計分")
        else:
            messagebox.showinfo("測驗結束", f"得分：{self.score} / {total}\n正確率：{(self.score / total) * 100:.1f}%")
        self.setup_main_menu()

    # =========================
    # 問答題複習功能：新增第 4 區塊
    # =========================
    def start_qa_review(self):
        if not self.qa_questions:
            messagebox.showerror(
                "問答題檔案錯誤",
                f"找不到或無法讀取問答題檔案：\n{self.qa_file_path}\n\n請確認 {os.path.basename(self.qa_file_path)} 與 question_qa_review.py 放在同一個資料夾。"
            )
            return

        self.qa_selected_questions = list(self.qa_questions)
        if self.qa_shuffle_var.get():
            random.shuffle(self.qa_selected_questions)

        self.current_qa_idx = 0
        self.show_qa_review_ui()

    def show_qa_review_ui(self):
        self.clear_frame()

        self.qa_frame = tk.Frame(self.root, padx=25, pady=18)
        self.qa_frame.pack(expand=True, fill="both")

        tk.Label(
            self.qa_frame,
            text="問答題複習模式",
            font=("Arial", 15, "bold"),
            fg="#E65100"
        ).pack(anchor="w", pady=(0, 8))

        self.qa_info_label = tk.Label(self.qa_frame, text="", font=("Arial", 10), fg="#616161")
        self.qa_info_label.pack(anchor="w", pady=(0, 8))

        # 可捲動內容區
        content_frame = tk.Frame(self.qa_frame)
        content_frame.pack(expand=True, fill="both")

        self.qa_canvas = tk.Canvas(content_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.qa_canvas.yview)
        self.qa_content = tk.Frame(self.qa_canvas)

        self.qa_content.bind(
            "<Configure>",
            lambda e: self.qa_canvas.configure(scrollregion=self.qa_canvas.bbox("all"))
        )
        self.qa_window = self.qa_canvas.create_window((0, 0), window=self.qa_content, anchor="nw")
        self.qa_canvas.configure(yscrollcommand=scrollbar.set)
        self.qa_canvas.bind(
            "<Configure>",
            lambda e: self.qa_canvas.itemconfigure(self.qa_window, width=e.width)
        )

        self.qa_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 滑鼠滾輪支援
        self.qa_canvas.bind("<Enter>", lambda event: self.qa_canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.qa_canvas.bind("<Leave>", lambda event: self.qa_canvas.unbind_all("<MouseWheel>"))

        # 按鈕列
        btn_frame = tk.Frame(self.qa_frame)
        btn_frame.pack(fill="x", pady=(12, 0))

        self._button(btn_frame, text="上一題", font_size=11, command=self.prev_qa_question, style="secondary").pack(side="left", fill="x", expand=True, padx=4)
        self._button(btn_frame, text="下一題", font_size=11, command=self.next_qa_question).pack(side="left", fill="x", expand=True, padx=4)
        self._button(btn_frame, text="返回主選單", font_size=11, command=self.setup_main_menu, style="secondary").pack(side="left", fill="x", expand=True, padx=4)

        self.load_qa_question()

    def _on_mousewheel(self, event):
        # Windows/macOS/Linux 常見情況支援
        try:
            self.qa_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _add_section(self, parent, title, content, title_color="#1A237E"):
        tk.Label(
            parent,
            text=title,
            font=("Arial", 12, "bold"),
            fg=title_color,
            anchor="w",
            justify="left"
        ).pack(fill="x", pady=(10, 2))

        tk.Label(
            parent,
            text=content if content else "無",
            font=("Arial", 11),
            wraplength=710,
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

    def load_qa_question(self):
        if not self.qa_selected_questions:
            return

        for widget in self.qa_content.winfo_children():
            widget.destroy()

        q = self.qa_selected_questions[self.current_qa_idx]
        total = len(self.qa_selected_questions)

        self.qa_info_label.config(
            text=f"進度：{self.current_qa_idx + 1} / {total}　|　題號：{q.get('id', '無')}　|　大題：{q.get('category', '未分類')}"
        )

        self._add_section(self.qa_content, "題目英文 Question EN", q.get("question_en", ""), "#0D47A1")
        self._add_section(self.qa_content, "題目中文 Question ZH", q.get("question_zh", ""), "#0D47A1")
        self._add_section(self.qa_content, "答案英文 Answer EN", q.get("answer_en", ""), "#1B5E20")
        self._add_section(self.qa_content, "答案中文 Answer ZH", q.get("answer_zh", ""), "#1B5E20")

        focus = q.get("exam_focus", [])
        if isinstance(focus, list):
            focus_text = "\n".join([f"{i + 1}. {item}" for i, item in enumerate(focus)])
        else:
            focus_text = str(focus)
        self._add_section(self.qa_content, "考試重點 Exam Focus", focus_text, "#B71C1C")

        # 每次切換題目時回到頂端
        self.qa_canvas.update_idletasks()
        self.qa_canvas.yview_moveto(0)

    def next_qa_question(self):
        if not self.qa_selected_questions:
            return
        if self.current_qa_idx < len(self.qa_selected_questions) - 1:
            self.current_qa_idx += 1
            self.load_qa_question()
        else:
            messagebox.showinfo("提示", "已經是最後一題")

    def prev_qa_question(self):
        if not self.qa_selected_questions:
            return
        if self.current_qa_idx > 0:
            self.current_qa_idx -= 1
            self.load_qa_question()
        else:
            messagebox.showinfo("提示", "已經是第一題")

    def clear_frame(self):
        # 避免返回主選單後滑鼠滾輪還綁在舊 canvas 上造成錯誤
        try:
            self.root.unbind_all("<MouseWheel>")
        except Exception:
            pass

        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()

    # 請確認預設 JSON 檔案與本程式放在同一個資料夾，或進入系統後使用「匯入題庫 JSON」載入自己的題庫。
    # 1. finaltest_question.json：預設選擇題題庫
    # 2. wlan_qa_review_N_Q.json：預設問答題複習資料
    app = QuizGUI(root, "finaltest_question.json", "wlan_qa_review_N_Q.json")

    root.mainloop()
