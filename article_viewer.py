from tkinter import Tk
from article_components import create_layout
from article_handlers import open_article, search_articles, delete_oldest_articles

class ArticleViewer:
    def __init__(self, master, db_manager):
        self.db_manager = db_manager
        self.root = master
        self.root.title("HoYoLAB 文章檢視器 - 搜尋功能版")
        self.root.geometry("1200x600")

        # 初始化 GUI 組件與功能綁定
        self.keyword_var, self.tree = create_layout(
            self.root,
            search_command=self.search,
            delete_command=self.delete_oldest,
            tree_double_click=self.open_url
        )


        # 預設載入資料
        self.refresh()

    def open_url(self, event):
        open_article(self.tree)

    def search(self):
        search_articles(self.tree, self.db_manager, self.keyword_var.get())

    def delete_oldest(self):
        delete_oldest_articles(self.tree, self.db_manager, self.keyword_var.get())

    def refresh(self):
        from article_handlers import refresh_table
        refresh_table(self.tree, self.db_manager.fetch_articles())

    def run(self):
        pass  # 如果你用的是 Toplevel，不需要呼叫 mainloop()
