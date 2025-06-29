from database import DatabaseManager
from scraper import HoYoLabScraper
from gui import HoYoLabGUI

if __name__ == "__main__":
    db_manager = DatabaseManager()
    scraper = HoYoLabScraper(db_manager)
    gui = HoYoLabGUI(scraper, db_manager)
    try:
        gui.run()
    finally:
        scraper.close()        # 釋放 WebDriver
        db_manager.close()     # 釋放資料庫連線（假設有 close 方法）
