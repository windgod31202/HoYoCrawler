from config import URL, SCROLL_PAUSE_TIME
from utils import parse_post_time
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup
import webbrowser


class HoYoLabScraper:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.driver = None  # 延遲初始化

    def _init_driver(self):
        if self.driver is None:
            options = Options()
            options.add_experimental_option("detach", True)
            options.add_argument("--disable-blink-features=AutomationControlled")
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(URL)

    # 加在類別裡面
    def open_website(self):
        try:
            webbrowser.open(URL)
        except Exception as e:
            print(f"[錯誤] 無法開啟瀏覽器: {e}")

    def get_article_timestamp(self, url):
        if self.driver is None:
            self._init_driver()

        try:
            self.driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            author_info = soup.find('p', class_='mhy-article-page-author-header__info')

            if author_info:
                raw_text = author_info.get_text(separator=' ', strip=True)
                post_time = parse_post_time(raw_text)
                if post_time:
                    print(f"🔎 解析時間: {post_time}")
                    self.driver.get(URL)
                    time.sleep(3)
                    return post_time
                else:
                    print("[警告] 無法解析發佈時間，使用目前時間代替")
            else:
                print("[警告] 找不到 author_info 節點，使用目前時間代替")

            self.driver.get(URL)
            time.sleep(3)
        except Exception as e:
            print(f"[錯誤] 抓取文章時間失敗：{e}")
            try:
                self.driver.get(URL)
                time.sleep(3)
            except:
                pass
        return datetime.now()
    
    def start_scraping(self, existing_urls, save_callback, log_callback, stop_event):
        self._init_driver()  # 這裡確保driver已經啟動

        existing_urls = self.db_manager.fetch_existing_urls()
        i = 0
        max_empty_scrolls = 3
        empty_scrolls = 0

        while not stop_event.is_set():
            try:
                wait = WebDriverWait(self.driver, 10)
                news_cards = wait.until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "mhy-news-card"))
                )

                if i >= len(news_cards):
                    log_callback("\n🔄 模擬滾動，抓取更多文章中...\n")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(SCROLL_PAUSE_TIME)

                    new_cards = self.driver.find_elements(By.CLASS_NAME, "mhy-news-card")
                    if len(new_cards) <= len(news_cards):
                        empty_scrolls += 1
                    else:
                        empty_scrolls = 0

                    if empty_scrolls >= max_empty_scrolls:
                        log_callback("✅ 沒有更多新文章，結束抓取。\n")
                        break

                    continue

                card = news_cards[i]
                try:
                    link_element = card.find_element(By.TAG_NAME, "a")
                    raw_title = link_element.text.strip()
                    url = link_element.get_attribute("href")
                    real_title = raw_title.splitlines()[0].strip() if "\n" in raw_title else raw_title

                    if url not in existing_urls:
                        article_datetime = self.get_article_timestamp(url)
                        if self.db_manager.save_article(real_title, url, article_datetime.strftime("%Y-%m-%d %H:%M:%S")):
                            existing_urls.add(url)
                            log_callback(f"新增文章: {real_title}\n")
                    else:
                        log_callback(f"[略過] 已存在網址：{url}\n")
                except StaleElementReferenceException:
                    log_callback(f"[警告] 第 {i+1} 篇卡片失效，跳過\n")
                except Exception as e:
                    log_callback(f"[錯誤] 第 {i+1} 篇處理失敗: {e}\n")

                i += 1

            except Exception as e:
                log_callback(f"[致命錯誤] 無法載入卡片清單: {e}\n")
                break

        log_callback("🔚 抓取流程結束\n")

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception:
            pass