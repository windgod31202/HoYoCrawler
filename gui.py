import threading
import tkinter as tk
from tkinter import messagebox

class HoYoLabGUI:
    def __init__(self, master, scraper, db_manager):
        self.scraper = scraper
        self.db_manager = db_manager
        self.stop_event = threading.Event()

        self.root = master  # 直接使用傳入的視窗（可能是Toplevel）
        self.root.title("HoYoLAB 自動爬文")
        self.root.geometry("500x300")

        self.info_label = tk.Label(self.root, text="請先在瀏覽器登入 HoYoLAB，完成後按開始")
        self.info_label.pack(pady=5)

        self.log_text = tk.Text(self.root, height=10, width=60)
        self.log_text.pack(pady=5)

        self.start_button = tk.Button(self.root, text="開始爬文", command=self.on_start)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="停止爬文", command=self.on_stop, state="disabled")
        self.stop_button.pack(pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def append_log(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def on_start(self):
        self.stop_event.clear()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.info_label.config(text="請在瀏覽器登入完成，爬文開始中...")

        threading.Thread(target=self.scraper.start_scraping,
                         args=(self.db_manager.fetch_existing_urls(),
                               self.db_manager.save_article,
                               lambda msg: self.root.after(0, self.append_log, msg),
                               self.stop_event),
                         daemon=True).start()

    def on_stop(self):
        self.stop_event.set()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.info_label.config(text="爬文已停止")

    def on_close(self):
        if messagebox.askokcancel("結束", "確定要結束程式嗎？"):
            self.stop_event.set()
            try:
                self.scraper.close()
            except Exception:
                pass
            self.root.destroy()

    def run(self):
        self.root.mainloop()
