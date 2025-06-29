import re
from datetime import datetime

def format_timestamp(timestamp):
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%Y/%m/%d")
    except Exception:
        return timestamp

def clean_title(title):
    return re.sub(r"\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b", "", title).strip()
