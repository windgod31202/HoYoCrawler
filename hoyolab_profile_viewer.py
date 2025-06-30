import sqlite3
import tkinter as tk
from tkinter import ttk
import webbrowser
from PIL import Image, ImageTk
import requests
from io import BytesIO

DB_PATH = "posts.db"

def show_article(event):
    selected_item = tree.focus()
    if not selected_item:
        return

    values = tree.item(selected_item)["values"]
    title, author, date, url = values

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM articles WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()

    content = result[0] if result else "[無內文]"

    popup = tk.Toplevel(root)
    popup.title(f"📄 {title}")
    popup.geometry("800x600")

    label_title = tk.Label(popup, text=title, font=("Microsoft JhengHei", 16, "bold"), wraplength=760, justify="left")
    label_title.pack(padx=10, pady=10, anchor="w")

    text_frame = tk.Frame(popup)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Microsoft JhengHei", 12), yscrollcommand=scrollbar.set)
    text_widget.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    # 🔽 圖片暫存（防止被垃圾回收）
    image_refs = []

    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("[圖片]:"):
            image_url = line.replace("[圖片]:", "").strip()
            try:
                response = requests.get(image_url, timeout=5)
                image_data = Image.open(BytesIO(response.content)).convert("RGBA")

                # 設定統一寬度
                fixed_width = 700
                w, h = image_data.size
                if w > 0 and h > 0:
                    ratio = fixed_width / w
                    new_width = fixed_width
                    new_height = int(h * ratio)
                    image_data = image_data.resize((new_width, new_height), Image.LANCZOS)

                    photo = ImageTk.PhotoImage(image_data)
                    text_widget.image_create(tk.END, image=photo)
                    text_widget.insert(tk.END, "\n")
                    image_refs.append(photo)  # 避免被垃圾回收
                else:
                    text_widget.insert(tk.END, f"[圖片尺寸錯誤]: {image_url}\n")
            except Exception as e:
                text_widget.insert(tk.END, f"[無法載入圖片]: {image_url}\n")
        elif line.startswith("[YouTube影片]:"):
            video_url = line.replace("[YouTube影片]:", "").strip()
            text_widget.insert(tk.END, f"▶ YouTube 影片：{video_url}\n")
            text_widget.tag_add(video_url, f"{float(text_widget.index(tk.END)) - 1} linestart", tk.END)
            text_widget.tag_config(video_url, foreground="blue", underline=True)
            text_widget.tag_bind(video_url, "<Button-1>", lambda e, url=video_url: webbrowser.open(url))
        else:
            text_widget.insert(tk.END, line + "\n")

    text_widget.config(state=tk.DISABLED)
    popup.image_refs = image_refs  # 綁定到 popup 防止 GC

def load_articles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, author, date, url FROM articles ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()

    for i, row in enumerate(rows):
        tag = "evenrow" if i % 2 == 0 else "oddrow"
        tree.insert("", "end", values=row, tags=(tag,))

# 初始化主視窗
root = tk.Tk()
root.title("🌟 HoYoLAB 文章資料瀏覽器")
root.geometry("1000x600")
root.configure(bg="#f2f2f2")

# 標題文字
title_label = tk.Label(root, text="HoYoLAB 文章資料瀏覽器", font=("Microsoft JhengHei", 20, "bold"), bg="#f2f2f2", fg="#333")
title_label.pack(pady=10)

# 標題欄位
columns = ("標題", "作者", "日期", "文章網址")
tree_frame = tk.Frame(root, bg="#f2f2f2")
tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

tree = ttk.Treeview(
    tree_frame,
    columns=columns,
    show="headings",
    yscrollcommand=tree_scroll_y.set,
    xscrollcommand=tree_scroll_x.set
)

tree_scroll_y.config(command=tree.yview)
tree_scroll_x.config(command=tree.xview)

# 表頭設定
style = ttk.Style()
style.theme_use("default")

style.configure("Treeview",
    background="#ffffff",
    foreground="#000000",
    rowheight=28,
    fieldbackground="#ffffff",
    font=("Microsoft JhengHei", 11)
)

style.configure("Treeview.Heading",
    font=("Microsoft JhengHei", 12, "bold"),
    background="#e1e1e1"
)

style.map("Treeview", background=[("selected", "#cfe2f3")])

tree.tag_configure("evenrow", background="#ffffff")
tree.tag_configure("oddrow", background="#f7f7f7")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="w", width=240 if col == "標題" else 120)

tree.pack(fill=tk.BOTH, expand=True)

# 綁定點擊事件
tree.bind("<Double-1>", show_article)

# 載入資料
load_articles()

# 主迴圈
root.mainloop()
