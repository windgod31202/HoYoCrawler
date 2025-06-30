import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from gui import HoYoLabGUI
from article_viewer import ArticleViewer
from database import DatabaseManager
from scraper import HoYoLabScraper

class LauncherApp:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.scraper = HoYoLabScraper(db_manager)

        self.root = tk.Tk()
        self.root.title("🚀 HoYoLAB 啟動器")
        self.root.geometry("400x350")
        self.root.configure(bg="#f5f5f5")

        self.label = tk.Label(
            self.root,
            text="請選擇要啟動的功能",
            font=("Microsoft JhengHei", 14, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        self.label.pack(pady=(30, 15))

        icon_path = os.path.join(os.path.dirname(__file__), "icon")

        # Pillow 9.1.0以後版本
        self.scraper_img = Image.open(os.path.join(icon_path, "scraper_icon.png")).resize((32, 32), Image.Resampling.LANCZOS)
        self.scraper_photo = ImageTk.PhotoImage(self.scraper_img)

        self.viewer_img = Image.open(os.path.join(icon_path, "viewer_icon.png")).resize((32, 32), Image.Resampling.LANCZOS)
        self.viewer_photo = ImageTk.PhotoImage(self.viewer_img)

        button_style = {
            "font": ("Microsoft JhengHei", 12),
            "bg": "#4CAF50",
            "fg": "white",
            "activebackground": "#45a049",
            "activeforeground": "white",
            "relief": "flat",
            "width": 250,
            "height": 40,
            "bd": 0,
            "cursor": "hand2",
            "compound": "left",
            "padx": 10
        }

        self.start_scraper_button = tk.Button(
            self.root,
            text="啟動爬文程式",
            image=self.scraper_photo,
            command=self.launch_scraper_gui,
            **button_style
        )
        self.start_scraper_button.pack(pady=10)

        self.start_viewer_button = tk.Button(
            self.root,
            text="啟動文章檢視器",
            image=self.viewer_photo,
            command=self.launch_viewer_gui,
            **button_style
        )
        self.start_viewer_button.pack(pady=5)

        self.scraper_window = None
        self.viewer_window = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def launch_scraper_gui(self):
        if self.scraper_window is None or not self.scraper_window.winfo_exists():
            self.scraper_window = tk.Toplevel(self.root)
            gui = HoYoLabGUI(self.scraper_window, self.scraper, self.db_manager)
            gui.run()
        else:
            messagebox.showinfo("提示", "爬文程式視窗已開啟")

    def launch_viewer_gui(self):
        if self.viewer_window is None or not self.viewer_window.winfo_exists():
            self.viewer_window = tk.Toplevel(self.root)
            viewer = ArticleViewer(self.viewer_window, self.db_manager)
            viewer.run()
        else:
            messagebox.showinfo("提示", "文章檢視器視窗已開啟")

    def on_close(self):
        if messagebox.askokcancel("結束", "確定要結束啟動器嗎？"):
            try:
                self.scraper.close()
            except Exception:
                pass
            try:
                self.db_manager.close()
            except Exception:
                pass
            self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    db_manager = DatabaseManager()
    app = LauncherApp(db_manager)
    app.run()
