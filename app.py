import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime

# ============================================================
# 配置
# ============================================================

CURRENT_SEASON_MAPS = [
    {"players": 2, "korean": "오디세이",       "english": "Odyssey",        "version": "RE 2.0"},
    {"players": 2, "korean": "컬러리스 페이트", "english": "Colorless Fate", "version": "1.1"},
    {"players": 3, "korean": "아이올로스",     "english": "Aiolos",         "version": "1.0b"},
    {"players": 4, "korean": "녹아웃",         "english": "KnockOut",       "version": "1.4"},
    {"players": 4, "korean": "백 룸",          "english": "Backrooms",      "version": "1.0"},
    {"players": 4, "korean": "애티튜드",       "english": "Attitude",       "version": "SE 2.1"},
    {"players": 4, "korean": "옥타곤",         "english": "Octagon",        "version": "SE 2.0"},
]

HOME_URL = "http://eloboard.com/"
DATA_URL = "http://eloboard.com/men/bbs/board.php?bo_table=map_stac"

# ============================================================
# 数据抓取
# ============================================================

def normalize_name(name):
    return re.sub(r'\s+', '', name).lower()

def find_map_data(map_info, maps_data):
    target_korean = normalize_name(map_info["korean"])
    target_english = normalize_name(map_info["english"])
    for name, data in maps_data.items():
        normalized = normalize_name(name)
        if target_korean in normalized or normalized in target_korean:
            return name, data
        if target_english in normalized or normalized in target_english:
            return name, data
    return None, None

@st.cache_data(ttl=3600)  # 缓存1小时
def fetch_and_parse():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": DATA_URL,
    }
    try:
        session = requests.Session()
        session.get(HOME_URL, headers=headers, timeout=30)
        resp = session.get(DATA_URL, headers=headers, timeout=30)
        resp.encoding = "utf-8"
        if resp.status_code != 200 or len(resp.text) < 1000:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 2:
            return None

        table = tables[1]
        rows = table.find_all("tr")
        maps_data = {}
        i = 0
        while i < len(rows):
            cells = rows[i].find_all(["td", "th"])
            if len(cells) >= 4:
                map_cell = cells[0].get_text(strip=True)
                match = re.match(r'(.+?)\((\d+)\)', map_cell)
                if match:
                    map_name = match.group(1).strip()
                    total_games = int(match.group(2))

                    def parse_race(text):
                        m = re.search(r'(\d+)승\s*(\d+)패\(([\d.]+)%\)', text)
                        if m:
                            return {"wins": int(m.group(1)), "losses": int(m.group(2)), "winrate": float(m.group(3))}
                        return {"wins": 0, "losses": 0, "winrate": 0.0}

                    z = parse_race(cells[1].get_text(strip=True))
                    p = parse_race(cells[2].get_text(strip=True))
                    t = parse_race(cells[3].get_text(strip=True))

                    matchups = {}
                    if i + 1 < len(rows):
                        next_cells = rows[i + 1].find_all(["td", "th"])
                        if len(next_cells) >= 4:
                            for idx in [1, 2, 3]:
                                text = next_cells[idx].get_text(strip=True)
                                for m in re.finditer(r'([ZPT])-([ZPT])\s*:\s*(\d+)승\s*(\d+)패\(([\d.]+)%\)', text):
                                    key = f"{m.group(1)}v{m.group(2)}"
                                    matchups[key] = {"wins": int(m.group(3)), "losses": int(m.group(4)), "winrate": float(m.group(5))}
                        i += 1

                    maps_data[map_name] = {
                        "total_games": total_games, "zerg": z, "protoss": p, "terran": t, "matchups": matchups
                    }
            i += 1
        return maps_data
    except Exception as e:
        return None

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="SC:BW 地图数据统计",
    page_icon="⚔️",
    layout="wide"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #334155;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #60a5fa;
        font-size: 2rem;
    }
    .main-header p {
        color: #94a3b8;
    }
    .metric-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #334155;
    }
    .winrate-high { color: #22c55e; font-weight: bold; }
    .winrate-low { color: #f97316; font-weight: bold; }
    .balance-good { color: #22c55e; }
    .balance-warn { color: #fbbf24; }
    .balance-bad { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 主页面
# ============================================================

st.markdown('<div class="main-header"><h1>⚔️ StarCraft: Brood War 地图数据统计</h1>'
            f'<p>数据来源: eloboard.com | 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p></div>',
            unsafe_allow_html=True)

# 获取数据
with st.spinner("正在获取最新数据..."):
    maps_data = fetch_and_parse()

if not maps_data:
    st.error("❌ 数据获取失败，请稍后刷新重试")
    st.stop()

st.success(f"✅ 成功获取 {len(maps_data)} 张地图数据！")

# ============================================================
# Tab 布局
# ============================================================

tab1, tab2, tab3 = st.tabs(["📊 赛季地图详情", "⚔️ 种族对抗总览", "🗺️ 全部地图排名"])

# ---- Tab 1: 赛季地图 ----
with tab1:
    st.subheader("当前赛季地图统计")

    for map_info in CURRENT_SEASON_MAPS:
        found_name, map_data = find_map_data(map_info, maps_data)

        with st.expander(
            f"({map_info['players']}人) {map_info['korean']} ({map_info['english']}) {map_info['version']}",
            expanded=True
        ):
            if map_data and map_data["total_games"] > 0:
                z, p, t = map_data["zerg"], map_data["protoss"], map_data["terran"]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("总场次", f"{map_data['total_games']:,}")
                col2.metric("🟤 Zerg 胜率", f"{z['winrate']}%", delta=f"{z['winrate']-50:.1f}%")
                col3.metric("🔵 Protoss 胜率", f"{p['winrate']}%", delta=f"{p['winrate']-50:.1f}%")
                col4.metric("🔴 Terran 胜率", f"{t['winrate']}%", delta=f"{t['winrate']-50:.1f}%")

                st.markdown("#### 对战详情")
                matchup_data = []
                for key in ["ZvT", "ZvP", "PvZ", "PvT", "TvZ", "TvP"]:
                    if key in map_data["matchups"]:
                        d = map_data["matchups"][key]
                        matchup_data.append({
                            "对战": key, "胜场": d["wins"], "负场": d["losses"], "胜率": d["winrate"]
                        })
                if matchup_data:
                    df = pd.DataFrame(matchup_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                # 平衡性
                diff = max(z['winrate'], p['winrate'], t['winrate']) - min(z['winrate'], p['winrate'], t['winrate'])
                if diff <= 5: bal = "✅ 非常平衡"
                elif diff <= 10: bal = "🟡 较为平衡"
                elif diff <= 15: bal = "🟠 略有失衡"
                else: bal = "🔴 明显失衡"
                st.markdown(f"**平衡性评估：** {bal} (最大差距 {diff:.1f}%)")
            else:
                st.warning("⚠️ 暂无数据（地图可能尚未被收录）")

# ---- Tab 2: 种族对抗总览 ----
with tab2:
    st.subheader("当前赛季种族对抗总览")

    matchup_totals = {}
    for map_info in CURRENT_SEASON_MAPS:
        _, data = find_map_data(map_info, maps_data)
        if data:
            for key, val in data.get("matchups", {}).items():
                if key not in matchup_totals:
                    matchup_totals[key] = {"wins": 0, "losses": 0}
                matchup_totals[key]["wins"] += val["wins"]
                matchup_totals[key]["losses"] += val["losses"]

    if matchup_totals:
        rows = []
        for key in ["ZvT", "ZvP", "PvZ", "PvT", "TvZ", "TvP"]:
            if key in matchup_totals:
                d = matchup_totals[key]
                total = d["wins"] + d["losses"]
                wr = (d["wins"] / total * 100) if total > 0 else 0
                rows.append({"对战": key, "总胜场": d["wins"], "总负场": d["losses"], "胜率(%)": round(wr, 1)})

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 进度条可视化
        st.markdown("#### 胜率可视化")
        for _, row in df.iterrows():
            wr = row["胜率(%)"]
            color = "green" if wr >= 50 else "orange"
            st.markdown(f"**{row['对战']}** ({wr}%)")
            st.progress(wr / 100)

# ---- Tab 3: 全部地图 ----
with tab3:
    st.subheader("全部地图概览（按场次排序）")

    all_rows = []
    for name, data in sorted(maps_data.items(), key=lambda x: x[1]["total_games"], reverse=True):
        z_wr = data["zerg"]["winrate"]
        p_wr = data["protoss"]["winrate"]
        t_wr = data["terran"]["winrate"]
        diff = max(z_wr, p_wr, t_wr) - min(z_wr, p_wr, t_wr)
        bal = "✅" if diff <= 5 else "🟡" if diff <= 10 else "🟠" if diff <= 15 else "🔴"
        all_rows.append({
            "地图名": name, "场次": data["total_games"],
            "Z胜率": z_wr, "P胜率": p_wr, "T胜率": t_wr, "平衡度": bal
        })

    df_all = pd.DataFrame(all_rows)
    st.dataframe(df_all, use_container_width=True, hide_index=True)

# 页脚
st.markdown("---")
st.markdown("<p style='text-align:center; color:#64748b;'>⚔️ StarCraft: Brood War Map Stats Tool | Data from eloboard.com</p>",
            unsafe_allow_html=True)