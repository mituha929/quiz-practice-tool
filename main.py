import tkinter as tk

from gui.main_window import QuizApp


def main():
    root = tk.Tk()
    app = QuizApp(root, "finaltest_question.json", "wlan_qa_review_N_Q.json")
    root.mainloop()


if __name__ == "__main__":
    main()
