from datetime import datetime, timedelta
import re

def parse_post_time(time_str):
    now = datetime.now()
    if m := re.match(r'(\d+)\s*天前', time_str):
        return now - timedelta(days=int(m[1]))
    elif m := re.match(r'(\d+)\s*小時前', time_str):
        return now - timedelta(hours=int(m[1]))
    elif m := re.match(r'(\d+)\s*分鐘前', time_str):
        return now - timedelta(minutes=int(m[1]))
    elif m := re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', time_str):
        y, mo, d = map(int, m.groups())
        return datetime(y, mo, d)
    elif m := re.match(r'(\d{1,2})[-/](\d{1,2})', time_str):
        mo, d = map(int, m.groups())
        return datetime(now.year, mo, d)
    return None
