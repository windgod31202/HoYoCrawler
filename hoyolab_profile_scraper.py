from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta  # 請確保這個在檔案最上方已經有匯入
import sqlite3
from config import TARGET_USER_POSTS_URL, SCROLL_PAUSE_TIME

def init_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    return webdriver.Chrome(options=options)

def init_db(db_path="posts.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            author TEXT,
            date TEXT,
            content TEXT
        )
    """)
    conn.commit()
    return conn

def add_article_to_db(conn, url, title, author, date, content):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO articles (url, title, author, date, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (url, title, author, date, content))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def wait_for_article_cards(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.mhy-article-card")
            )
        )
        print("[成功] 找到文章卡片")
    except:
        print("[錯誤] 超時找不到文章卡片")

def scroll_to_bottom(driver, pause_time=1.5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause_time)

def extract_post_links(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.mhy-article-card-wrapper.mhy-account-center-post-card")
            )
        )
    except:
        print("[錯誤] 未找到文章卡片元素，將嘗試掃描全部 <a> 連結")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set()
    outer_cards = soup.select("div.mhy-article-card-wrapper.mhy-account-center-post-card")
    for outer_card in outer_cards:
        inner_card = outer_card.select_one("div.mhy-article-card")
        if inner_card:
            a_tag = inner_card.find("a", href=True)
            if a_tag:
                href = a_tag['href']
                if href.startswith("/article/") and href[9:].isdigit():
                    full_url = "https://www.hoyolab.com" + href
                    links.add(full_url)
    a_tags = soup.find_all("a", href=True)
    for a in a_tags:
        href = a['href']
        if href.startswith("/article/") and href[9:].isdigit():
            full_url = "https://www.hoyolab.com" + href
            links.add(full_url)
    return list(links)

def extract_post_details(driver, url):
    WAIT_TIMEOUT = 15
    try:
        driver.get(url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        time.sleep(2)

        title_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        title = title_element.text.strip()

        content_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mhy-article-page__content"))
        )

        # 使用 BeautifulSoup 處理完整 HTML 內容
        soup = BeautifulSoup(content_element.get_attribute("innerHTML"), "html.parser")


        # 處理所有圖片標籤，不限 class 結構
        img_count = 0
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src and src.startswith("http"):
                img.insert_after(soup.new_string(f"\n[圖片]: {src}\n"))
                img_count += 1
        print(f"✅ 共發現 {img_count} 張圖片")

        # ✅ 處理 YouTube iframe
        youtube_count = 0
        for iframe in soup.select("iframe.mhy-video-frame.ql-frame"):
            src = iframe.get("src")
            if src and "youtube" in src:
                iframe.insert_after(soup.new_string(f"\n[YouTube影片]: {src}\n"))
                youtube_count += 1
        print(f"✅ 共發現 {youtube_count} 則 YouTube 影片")

        # ✅ 取得純文字（含圖片與影片的附註）
        content = soup.get_text("\n").strip()

        # 作者
        try:
            author_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".mhy-account-title__name"))
            )
            author = author_element.text.strip()
        except:
            author = "[未知]"

        # 時間處理
        try:
            date_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.mhy-article-page-author-header__info"))
            )
            date_raw = date_element.text.strip()
            now = datetime.now()

            if "剛剛" in date_raw or "分鐘前" in date_raw or "小時前" in date_raw:
                date = now.strftime("%Y/%m/%d")
            elif "天前" in date_raw:
                days_ago = int(date_raw.replace("天前", "").strip())
                date = (now - timedelta(days=days_ago)).strftime("%Y/%m/%d")
            elif "/" in date_raw and date_raw.count("/") == 1:
                date = f"{now.year}/{date_raw}"
            else:
                date = date_raw
        except:
            date = "[未知]"

        # 除錯列印
        print(f"\n🔗 文章網址: {url}")
        print("📌 標題:", title)
        print("👤 作者:", author)
        print("📅 日期:", date)
        print("📝 內文:", content[:200] + "..." if content else "[內文缺失]")
        print("-" * 80)

        return title, author, date, content

    except Exception as e:
        print(f"[錯誤] 無法抓取文章 {url}，錯誤原因：{e}")
        print("-" * 80)
        return None, None, None, None
    
def scroll_and_collect_all_links(driver, max_scrolls=100, pause_time=2, max_no_growth=5):
    all_seen_links = set()
    no_growth_count = 0

    for i in range(max_scrolls):
        # 滾動底部以觸發載入
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)

        # 偽下拉補充滾動觸發
        driver.execute_script("window.scrollBy(0, -200);")
        time.sleep(1)

        # 抓取目前連結
        new_links = set(extract_post_links(driver))

        if len(new_links) > len(all_seen_links):
            newly_added = new_links - all_seen_links
            all_seen_links.update(new_links)
            print(f"第 {i+1} 次滾動，發現 {len(newly_added)} 個新連結（累計：{len(all_seen_links)}）")
            no_growth_count = 0
        else:
            no_growth_count += 1
            print(f"第 {i+1} 次滾動無新增，連續 {no_growth_count} 次無增長")

        # ✅ 檢查是否已經到底部
        try:
            footer_text = driver.find_element(By.CLASS_NAME, "mhy-load-next-core-content").text
            if "已經拉到底了" in footer_text:
                print("✅ 偵測到底部訊息『已經拉到底了』，結束滾動")
                break
        except:
            pass  # 可能還沒出現，忽略

        # ⚠️ 當「點擊載入更多」存在，表示還能載入 → 不中止
        try:
            more_text = driver.find_element(By.CLASS_NAME, "next-content").text
            if "點擊載入更多" in more_text:
                print("🔄 偵測到『點擊載入更多』存在，繼續滾動")
                continue
        except:
            pass  # 沒出現就略過

        # 🚫 若連續多次無增長就提前終止
        if no_growth_count >= max_no_growth:
            print("⚠️ 偵測到連續多次無新增連結，提早結束滾動")
            break

    return list(all_seen_links)

def update_article_content(conn, url, new_content):
    cursor = conn.cursor()
    cursor.execute("UPDATE articles SET content = ? WHERE url = ?", (new_content, url))
    conn.commit()

def fill_missing_article_content(conn, driver):
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM articles WHERE content IS NULL OR TRIM(content) = ''")
    rows = cursor.fetchall()

    if not rows:
        print("✅ 所有文章都有內容，不需補抓。")
        return

    print(f"🔍 發現 {len(rows)} 篇文章缺少內文，開始補抓...")

    for (url,) in rows:
        title, author, date, content = extract_post_details(driver, url)
        if content:
            update_article_content(conn, url, content)
            print(f"✅ 已補上文章：{url}")
        else:
            print(f"⚠️ 無法補上：{url}（可能已失效）")
        time.sleep(1)

def update_missing_images(conn, driver):
    cursor = conn.cursor()
    cursor.execute("SELECT url, content FROM articles")
    rows = cursor.fetchall()

    candidates = []
    for url, content in rows:
        if "[圖片]:" not in (content or ""):
            candidates.append(url)

    if not candidates:
        print("✅ 所有文章都有圖片或已確認無圖。")
        return

    print(f"🔍 準備檢查 {len(candidates)} 篇可能遺漏圖片的文章...")

    for url in candidates:
        print(f"🔍 重新檢查圖片：{url}")
        title, author, date, new_content = extract_post_details(driver, url)
        if new_content and "[圖片]:" in new_content:
            update_article_content(conn, url, new_content)
            print(f"✅ 已補上圖片：{url}")
        else:
            print(f"⚠️ 沒找到圖片：{url}")
        time.sleep(1)


def main():
    conn = init_db()
    driver = init_driver()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM articles")
        db_links = set(row[0] for row in cursor.fetchall())

        driver.get(TARGET_USER_POSTS_URL)
        time.sleep(3)

        all_links_seen = scroll_and_collect_all_links(driver, max_scrolls=10000, pause_time=SCROLL_PAUSE_TIME, max_no_growth=5)
        new_links = [link for link in all_links_seen if link not in db_links]
        print(f"🔎 從共 {len(all_links_seen)} 篇文章中發現 {len(new_links)} 篇新文章")

        for link in new_links:
            title, author, date, content = extract_post_details(driver, link)
            if title:
                added = add_article_to_db(conn, link, title, author, date, content)
                if added:
                    db_links.add(link)
            time.sleep(1)

        print(f"\n✅ 抓取完成，目前資料庫共 {len(db_links)} 篇文章")

        # ✅ 補抓遺漏內容
        fill_missing_article_content(conn, driver)
        # ✅ 補抓遺漏的圖片（content 裡面沒包含圖片連結）
        update_missing_images(conn, driver)

    finally:
        driver.quit()
        conn.close()

if __name__ == "__main__":
    main()
