import requests
from bs4 import BeautifulSoup
import re, os, json, time
from datetime import datetime

HOME_URL = "http://eloboard.com/"
DATA_URL = "http://eloboard.com/men/bbs/board.php?bo_table=map_stac"
SEASON_FILE = "season.json"
HISTORY_FILE = os.path.join("data", "history.json")

# ---------- 工具 ----------
def normalize_name(name):
    return re.sub(r'\s+', '', name).lower()

def load_season():
    with open(SEASON_FILE, encoding="utf-8") as f:
        return json.load(f)

def find_map_data(map_info, maps_data):
    tk, te = normalize_name(map_info["korean"]), normalize_name(map_info["english"])
    for name, data in maps_data.items():
        n = normalize_name(name)
        if tk in n or n in tk or te in n or n in te:
            return name, data
    return None, None

def _parse_race(text):
    m = re.search(r'(\d+)승\s*(\d+)패\(([\d.]+)%\)', text)
    return {"wins": int(m.group(1)), "losses": int(m.group(2)), "winrate": float(m.group(3))} \
        if m else {"wins": 0, "losses": 0, "winrate": 0.0}

# ---------- 抓取（带重试）----------
def fetch_page(retries=3, timeout=30):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": DATA_URL,
    }
    last_err = None
    for attempt in range(retries):
        try:
            s = requests.Session()
            s.get(HOME_URL, headers=headers, timeout=timeout)
            r = s.get(DATA_URL, headers=headers, timeout=timeout)
            r.encoding = "utf-8"
            if r.status_code == 200 and len(r.text) > 1000:
                return r.text
            last_err = f"status={r.status_code}"
        except Exception as e:
            last_err = str(e)
        time.sleep(2 * (attempt + 1))   # 指数退避
    print(f"[fetch_page] 全部重试失败: {last_err}")
    return None

# ---------- 解析 ----------
def parse_map_data(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        return {}
    rows = tables[1].find_all("tr")
    data, i = {}, 0
    while i < len(rows):
        cells = rows[i].find_all(["td", "th"])
        if len(cells) >= 4:
            mc = cells[0].get_text(strip=True)
            mm = re.match(r'(.+?)\((\d+)\)', mc)
            if mm:
                name, total = mm.group(1).strip(), int(mm.group(2))
                z = _parse_race(cells[1].get_text(strip=True))
                p = _parse_race(cells[2].get_text(strip=True))
                t = _parse_race(cells[3].get_text(strip=True))
                mu = {}
                if i + 1 < len(rows):
                    nc = rows[i + 1].find_all(["td", "th"])
                    if len(nc) >= 4:
                        for idx in (1, 2, 3):
                            for m in re.finditer(r'([ZPT])-([ZPT])\s*:\s*(\d+)승\s*(\d+)패\(([\d.]+)%\)',
                                                 nc[idx].get_text(strip=True)):
                                mu[f"{m.group(1)}v{m.group(2)}"] = {
                                    "wins": int(m.group(3)), "losses": int(m.group(4)), "winrate": float(m.group(5))}
                    i += 1
                data[name] = {"total_games": total, "zerg": z, "protoss": p, "terran": t, "matchups": mu}
        i += 1
    return data

# ---------- 主入口（返回状态，便于预警）----------
def scrape(retries=3):
    html = fetch_page(retries)
    if not html:
        return None, "network"      # 网络/反爬失败
    data = parse_map_data(html)
    if not data:
        return None, "structure"    # 网站改版，解析为 0
    return data, "ok"

# ---------- 平衡性评分（0-100，越高越平衡）----------
def balance_score(z, p, t, total):
    rates = [z, p, t]
    if 0 in rates or total < 50:
        return None                 # 样本不足
    diff = max(rates) - min(rates)
    score = max(0, 100 - diff * 4)  # 差距 25% → 0 分
    if total < 200:                 # 样本量惩罚
        score *= 0.85
    return round(score, 1)

def balance_label(score):
    if score is None: return ("nodata", "样本不足")
    if score >= 80:   return ("good", "非常平衡")
    if score >= 60:   return ("warn", "较为平衡")
    if score >= 40:   return ("mid",  "略有失衡")
    return ("bad", "明显失衡")

# ---------- 历史数据 ----------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_snapshot(data):
    """把当天赛季地图数据追加到历史（同一天覆盖）"""
    os.makedirs("data", exist_ok=True)
    season = load_season()
    today = datetime.now().strftime("%Y-%m-%d")
    snap = {"date": today, "maps": {}}
    for mi in season["maps"]:
        _, md = find_map_data(mi, data)
        if md and md["total_games"] > 0:
            snap["maps"][mi["english"]] = {
                "total": md["total_games"],
                "z": md["zerg"]["winrate"], "p": md["protoss"]["winrate"], "t": md["terran"]["winrate"],
            }
    history = [h for h in load_history() if h["date"] != today]
    history.append(snap)
    history.sort(key=lambda x: x["date"])
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return today