# article_components.py
from tkinter import Frame, Label, Entry, Button, Scrollbar, VERTICAL, HORIZONTAL, StringVar, BOTH, Y, X, LEFT, RIGHT, END
from tkinter import ttk

def create_layout(root, search_command, delete_command, tree_double_click):
    keyword_var = StringVar()

    main_frame = Frame(root)
    main_frame.pack(fill=BOTH, expand=True)

    left_frame = Frame(main_frame, padx=10, pady=10)
    left_frame.pack(side=LEFT, fill=Y)

    Label(left_frame, text="搜尋標題關鍵字", font=("Arial", 12)).pack(pady=5)
    Entry(left_frame, textvariable=keyword_var, font=("Arial", 12), width=20).pack(pady=5)
    Button(left_frame, text="查詢", command=search_command).pack(pady=10)
    Button(left_frame, text="刪除前5篇文章", command=delete_command, fg="red").pack(pady=10)

    right_frame = Frame(main_frame)
    right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    columns = ("標題", "日期", "網址")
    tree = ttk.Treeview(right_frame, columns=columns, show="headings")

    vsb = Scrollbar(right_frame, orient=VERTICAL, command=tree.yview)
    hsb = Scrollbar(right_frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill=Y)
    hsb.pack(side="bottom", fill=X)
    tree.pack(fill=BOTH, expand=True)

    tree.heading("標題", text="文章標題")
    tree.heading("日期", text="日期")
    tree.heading("網址", text="文章網址")

    tree.column("標題", anchor="w", width=400)
    tree.column("日期", anchor="center", width=100)
    tree.column("網址", anchor="w", width=400)

    tree.bind("<Double-1>", tree_double_click)

    return keyword_var, tree
