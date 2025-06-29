import webbrowser
from tkinter import messagebox
from article_utils import format_timestamp, clean_title

def open_article(event):
    tree = event.widget
    selected_item = tree.focus()
    if selected_item:
        url = tree.item(selected_item)["values"][2]
        webbrowser.open(url)
        
def refresh_table(tree, articles):
    for row in tree.get_children():
        tree.delete(row)

    for title, url, timestamp in articles:
        tree.insert("", "end", values=(clean_title(title), format_timestamp(timestamp), url))

def search_articles(tree, db_manager, keyword):
    articles = db_manager.fetch_articles(keyword)
    refresh_table(tree, articles)

def delete_oldest_articles(tree, db_manager, keyword):
    if messagebox.askyesno("確認刪除", "確定要刪除時間最早的前5篇文章嗎？"):
        count = db_manager.delete_oldest_articles(5)
        messagebox.showinfo("刪除完成", f"成功刪除 {count} 篇文章")
        refresh_table(tree, db_manager.fetch_articles(keyword))
