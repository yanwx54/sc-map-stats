import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
import plotly.graph_objects as go
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

RACE_META = {
    "zerg":    {"name": "Zerg",    "icon": "🟢", "cls": "zerg"},
    "protoss": {"name": "Protoss", "icon": "🔵", "cls": "protoss"},
    "terran":  {"name": "Terran",  "icon": "🔴", "cls": "terran"},
}

# ============================================================
# 数据抓取（已验证可用）
# ============================================================
def normalize_name(name):
    return re.sub(r'\s+', '', name).lower()

def find_map_data(map_info, maps_data):
    tk, te = normalize_name(map_info["korean"]), normalize_name(map_info["english"])
    for name, data in maps_data.items():
        n = normalize_name(name)
        if tk in n or n in tk or te in n or n in te:
            return name, data
    return None, None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_parse():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": DATA_URL,
    }
    try:
        s = requests.Session()
        s.get(HOME_URL, headers=headers, timeout=30)
        r = s.get(DATA_URL, headers=headers, timeout=30)
        r.encoding = "utf-8"
        if r.status_code != 200 or len(r.text) < 1000:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 2:
            return None
        rows = tables[1].find_all("tr")
        data = {}
        i = 0
        def pr(text):
            m = re.search(r'(\d+)승\s*(\d+)패\(([\d.]+)%\)', text)
            return {"wins": int(m.group(1)), "losses": int(m.group(2)), "winrate": float(m.group(3))} if m else {"wins":0,"losses":0,"winrate":0.0}
        while i < len(rows):
            cells = rows[i].find_all(["td", "th"])
            if len(cells) >= 4:
                mc = cells[0].get_text(strip=True)
                mm = re.match(r'(.+?)\((\d+)\)', mc)
                if mm:
                    name, total = mm.group(1).strip(), int(mm.group(2))
                    z, p, t = pr(cells[1].get_text(strip=True)), pr(cells[2].get_text(strip=True)), pr(cells[3].get_text(strip=True))
                    mu = {}
                    if i + 1 < len(rows):
                        nc = rows[i+1].find_all(["td", "th"])
                        if len(nc) >= 4:
                            for idx in (1,2,3):
                                for m in re.finditer(r'([ZPT])-([ZPT])\s*:\s*(\d+)승\s*(\d+)패\(([\d.]+)%\)', nc[idx].get_text(strip=True)):
                                    mu[f"{m.group(1)}v{m.group(2)}"] = {"wins":int(m.group(3)),"losses":int(m.group(4)),"winrate":float(m.group(5))}
                        i += 1
                    data[name] = {"total_games": total, "zerg": z, "protoss": p, "terran": t, "matchups": mu}
            i += 1
        return data
    except Exception:
        return None

# ============================================================
# HTML 渲染组件
# ============================================================
def wr_cls(wr):  return "high" if wr >= 50 else "low"

def balance_info(z, p, t):
    rates = [z, p, t]
    if 0 in rates: return ("nodata", "数据不足", 0)
    diff = max(rates) - min(rates)
    if diff <= 5:   return ("bal-good", "非常平衡", diff)
    if diff <= 10:  return ("bal-warn", "较为平衡", diff)
    if diff <= 15:  return ("bal-mid",  "略有失衡", diff)
    return ("bal-bad", "明显失衡", diff)

def race_box(key, d):
    m = RACE_META[key]
    return f"""
    <div class="race-box {m['cls']}">
      <div class="rb-label">{m['icon']} {m['name']}</div>
      <div class="rb-wr {wr_cls(d['winrate'])}">{d['winrate']:.1f}%</div>
      <div class="rb-wl">{d['wins']:,} 胜 / {d['losses']:,} 负</div>
      <div class="bar-track"><div class="bar-fill {wr_cls(d['winrate'])}" style="width:{d['winrate']:.1f}%"></div></div>
    </div>"""

def mu_row(key, d):
    return f"""
    <div class="mu-row">
      <span class="mu-label">{key}</span>
      <div class="bar-track mu-track"><div class="bar-fill {wr_cls(d['winrate'])}" style="width:{d['winrate']:.1f}%"></div></div>
      <span class="mu-wr {wr_cls(d['winrate'])}">{d['winrate']:.1f}%</span>
      <span class="mu-wl">{d['wins']:,}-{d['losses']:,}</span>
    </div>"""

def map_card(map_info, found_name, md):
    head = f"""
    <div class="map-head">
      <span class="map-players">{map_info['players']}人图</span>
      <span class="map-title">{map_info['korean']} <span class="map-en">{map_info['english']}</span> <span class="map-ver">{map_info['version']}</span></span>
    """
    if md and md["total_games"] > 0:
        z, p, t = md["zerg"], md["protoss"], md["terran"]
        bcls, btxt, diff = balance_info(z["winrate"], p["winrate"], t["winrate"])
        head += f'<span class="bal-badge {bcls}">{btxt} · 差{diff:.1f}%</span></div>'
        body = f'<div class="map-games">总场次 <b>{md["total_games"]:,}</b></div>'
        body += '<div class="race-grid">' + race_box("zerg", z) + race_box("protoss", p) + race_box("terran", t) + '</div>'
        if md["matchups"]:
            body += '<div class="mu-title">对战详情</div><div class="matchup-list">'
            for k in ["ZvT","ZvP","PvZ","PvT","TvZ","TvP"]:
                if k in md["matchups"]:
                    body += mu_row(k, md["matchups"][k])
            body += '</div>'
    else:
        head += '<span class="bal-badge bal-nodata">暂无数据</span></div>'
        body = '<div class="no-data">⚠️ 该地图尚未被 eloboard 收录</div>'
    return f'<div class="sc-card map-card">{head}{body}</div>'

def metric_card(label, value, sub, vcls=""):
    return f"""
    <div class="metric-card">
      <div class="mc-label">{label}</div>
      <div class="mc-value {vcls}">{value}</div>
      <div class="mc-sub">{sub}</div>
    </div>"""

# ============================================================
# 自定义 CSS（电竞仪表盘风格）
# ============================================================
CUSTOM_CSS = """
<style>
  .stApp { background: radial-gradient(1200px 600px at 50% -10%, #1e3a8a33, transparent), #0f172a; }
  #MainMenu, footer { visibility: hidden; }
  header[data-testid="stHeader"] { background: transparent; }
  .block-container { padding-top: 1rem; max-width: 1200px; }

  .hero { position: relative; border-radius: 20px; overflow: hidden; margin-bottom: 1.5rem;
          background: linear-gradient(135deg,#1e3a8a 0%,#312e81 50%,#0f172a 100%);
          border: 1px solid #334155; box-shadow: 0 20px 50px -20px #000a; }
  .hero img { width: 100%; display: block; opacity: .92; }
  .hero-text { padding: 1.4rem 2rem 1.6rem; text-align: center; }
  .hero-text h1 { margin:0; font-size: 2.1rem; font-weight: 800; letter-spacing:.04em;
          background: linear-gradient(90deg,#4ade80,#60a5fa,#f87171);
          -webkit-background-clip: text; background-clip: text; color: transparent; }
  .hero-text p { margin:.4rem 0 0; color:#94a3b8; font-size:.95rem; }

  .sc-card { background: rgba(30,41,59,.55); backdrop-filter: blur(10px);
          border: 1px solid rgba(148,163,184,.15); border-radius: 16px;
          padding: 1.3rem 1.5rem; margin-bottom: 1.2rem;
          box-shadow: 0 8px 30px -12px #000a; transition: transform .2s, border-color .2s; }
  .sc-card:hover { transform: translateY(-2px); border-color: rgba(96,165,250,.4); }

  .metric-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 1.6rem; }
  .metric-card { background: rgba(30,41,59,.6); border:1px solid rgba(148,163,184,.15);
          border-radius: 14px; padding: 1rem 1.2rem; text-align:center; }
  .mc-label { color:#94a3b8; font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; }
  .mc-value { font-size: 1.9rem; font-weight: 800; margin:.3rem 0; color:#f1f5f9; }
  .mc-value.high { color:#4ade80; } .mc-value.low { color:#f87171; } .mc-value.blue { color:#60a5fa; }
  .mc-sub { color:#64748b; font-size:.8rem; }

  .map-head { display:flex; align-items:center; gap:.7rem; flex-wrap:wrap; margin-bottom:.9rem; }
  .map-players { background:#334155; color:#cbd5e1; font-size:.75rem; font-weight:700;
          padding:.2rem .6rem; border-radius:6px; }
  .map-title { font-size:1.25rem; font-weight:700; color:#f1f5f9; flex:1; }
  .map-en { color:#60a5fa; font-weight:500; font-size:1rem; }
  .map-ver { color:#64748b; font-size:.85rem; }
  .map-games { color:#94a3b8; font-size:.9rem; margin-bottom:1rem; }
  .map-games b { color:#f1f5f9; font-size:1.1rem; }

  .bal-badge { font-size:.78rem; font-weight:700; padding:.3rem .7rem; border-radius:20px; }
  .bal-good { background:#22c55e22; color:#4ade80; border:1px solid #22c55e55; }
  .bal-warn { background:#fbbf2422; color:#fbbf24; border:1px solid #fbbf2455; }
  .bal-mid  { background:#f9731622; color:#fb923c; border:1px solid #f9731655; }
  .bal-bad  { background:#ef444422; color:#f87171; border:1px solid #ef444455; }
  .bal-nodata { background:#64748b22; color:#94a3b8; border:1px solid #64748b55; }

  .race-grid { display:grid; grid-template-columns: repeat(3,1fr); gap:.9rem; }
  .race-box { border-radius:12px; padding:.9rem 1rem; border:1px solid; }
  .race-box.zerg    { background:#4ade8010; border-color:#4ade8033; }
  .race-box.protoss { background:#60a5fa10; border-color:#60a5fa33; }
  .race-box.terran  { background:#f8717110; border-color:#f8717133; }
  .rb-label { font-size:.85rem; font-weight:600; color:#cbd5e1; }
  .rb-wr { font-size:1.8rem; font-weight:800; margin:.2rem 0; }
  .rb-wl { font-size:.8rem; color:#94a3b8; margin-bottom:.5rem; }

  .bar-track { width:100%; height:8px; background:rgba(255,255,255,.08); border-radius:99px; overflow:hidden; }
  .bar-fill { height:100%; border-radius:99px; transition: width 1s cubic-bezier(.4,0,.2,1); }
  .bar-fill.high { background:linear-gradient(90deg,#22c55e,#4ade80); box-shadow:0 0 10px #22c55e66; }
  .bar-fill.low  { background:linear-gradient(90deg,#f97316,#fbbf24); box-shadow:0 0 10px #f9731666; }
  .high { color:#4ade80; } .low { color:#fb923c; }

  .mu-title { margin:1.2rem 0 .6rem; color:#94a3b8; font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; }
  .matchup-list { display:grid; grid-template-columns: repeat(2,1fr); gap:.5rem 1.5rem; }
  .mu-row { display:flex; align-items:center; gap:.7rem; }
  .mu-label { width:42px; font-weight:700; color:#cbd5e1; font-size:.9rem; }
  .mu-track { flex:1; }
  .mu-wr { width:52px; text-align:right; font-weight:700; font-size:.9rem; }
  .mu-wl { width:80px; text-align:right; color:#64748b; font-size:.8rem; }
  .no-data { color:#94a3b8; padding:1rem 0; text-align:center; }

  .allmap-table { width:100%; border-collapse:collapse; }
  .allmap-table th { text-align:left; color:#94a3b8; font-size:.78rem; text-transform:uppercase;
          letter-spacing:.06em; padding:.7rem .8rem; border-bottom:2px solid #334155; }
  .allmap-table td { padding:.8rem; border-bottom:1px solid #1e293b; font-size:.92rem; color:#e2e8f0; }
  .allmap-table tr:hover td { background:rgba(255,255,255,.03); }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:.4rem; }
  .dot.good{background:#4ade80;} .dot.warn{background:#fbbf24;} .dot.mid{background:#fb923c;} .dot.bad{background:#f87171;}

  .stTabs [data-baseweb="tab-list"] { gap:.5rem; }
  .stTabs [data-baseweb="tab"] { background:rgba(30,41,59,.6); border-radius:10px; padding:.5rem 1.2rem; }
  .stTabs [aria-selected="true"] { background:linear-gradient(90deg,#1e3a8a,#312e81) !important; }
  @media (max-width:768px){ .metric-row{grid-template-columns:repeat(2,1fr);} .race-grid{grid-template-columns:1fr;} .matchup-list{grid-template-columns:1fr;} }
</style>
"""

# ============================================================
# 页面
# ============================================================
st.set_page_config(page_title="SC:BW 地图数据统计", page_icon="⚔️", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Hero 头部
if os.path.exists("banner.png"):
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.image("banner.png", use_container_width=True)
    st.markdown(f'<div class="hero-text"><h1>⚔️ StarCraft: Brood War 地图数据统计</h1>'
                f'<p>数据来源 eloboard.com · 更新于 {datetime.now().strftime("%Y-%m-%d %H:%M")}</p></div></div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="hero"><div class="hero-text" style="padding:2.5rem 2rem;">'
                f'<h1>⚔️ StarCraft: Brood War 地图数据统计</h1>'
                f'<p>数据来源 eloboard.com · 更新于 {datetime.now().strftime("%Y-%m-%d %H:%M")}</p></div></div>',
                unsafe_allow_html=True)

# 刷新按钮
if st.button("🔄 立即刷新数据", type="primary"):
    fetch_and_parse.clear()
    st.rerun()

maps_data = fetch_and_parse()
if not maps_data:
    st.error("❌ 数据获取失败，请稍后点击刷新重试")
    st.stop()

# ---- 顶部 Summary ----
season_games, best, worst = 0, None, None
for mi in CURRENT_SEASON_MAPS:
    _, md = find_map_data(mi, maps_data)
    if md and md["total_games"] > 0:
        season_games += md["total_games"]
        d = max(md["zerg"]["winrate"], md["protoss"]["winrate"], md["terran"]["winrate"]) - \
            min(md["zerg"]["winrate"], md["protoss"]["winrate"], md["terran"]["winrate"])
        if best is None or d < best[1]:  best = (mi["english"], d)
        if worst is None or d > worst[1]: worst = (mi["english"], d)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(metric_card("收录地图", str(len(maps_data)), "eloboard 全站", "blue"), unsafe_allow_html=True)
c2.markdown(metric_card("赛季总场次", f"{season_games:,}", "当前地图池", "blue"), unsafe_allow_html=True)
c3.markdown(metric_card("最平衡", best[0] if best else "-", f"差距 {best[1]:.1f}%" if best else "", "high"), unsafe_allow_html=True)
c4.markdown(metric_card("最失衡", worst[0] if worst else "-", f"差距 {worst[1]:.1f}%" if worst else "", "low"), unsafe_allow_html=True)

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["📊 赛季地图详情", "⚔️ 种族对抗总览", "🗺️ 全部地图排名"])

with tab1:
    for mi in CURRENT_SEASON_MAPS:
        fn, md = find_map_data(mi, maps_data)
        st.markdown(map_card(mi, fn, md), unsafe_allow_html=True)

with tab2:
    totals = {}
    for mi in CURRENT_SEASON_MAPS:
        _, md = find_map_data(mi, maps_data)
        if md:
            for k, v in md.get("matchups", {}).items():
                totals.setdefault(k, {"wins":0,"losses":0})
                totals[k]["wins"] += v["wins"]; totals[k]["losses"] += v["losses"]

    rows = []
    for k in ["ZvT","ZvP","PvZ","PvT","TvZ","TvP"]:
        if k in totals:
            d = totals[k]; tot = d["wins"]+d["losses"]
            wr = round(d["wins"]/tot*100, 1) if tot else 0
            rows.append({"matchup": k, "wins": d["wins"], "losses": d["losses"], "wr": wr})

    # HTML 大卡片
    html = '<div class="sc-card">'
    for r in rows:
        html += f"""
        <div class="mu-row" style="margin-bottom:.7rem;">
          <span class="mu-label" style="width:54px;font-size:1.05rem;">{r['matchup']}</span>
          <div class="bar-track mu-track" style="height:12px;"><div class="bar-fill {wr_cls(r['wr'])}" style="width:{r['wr']}%"></div></div>
          <span class="mu-wr {wr_cls(r['wr'])}" style="width:60px;font-size:1.05rem;">{r['wr']}%</span>
          <span class="mu-wl" style="width:110px;">{r['wins']:,} - {r['losses']:,}</span>
        </div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Plotly 图表
    if rows:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=[r["matchup"] for r in rows], x=[r["wr"] for r in rows], orientation="h",
            marker_color=["#4ade80" if r["wr"] >= 50 else "#fb923c" for r in rows],
            text=[f'{r["wr"]}%' for r in rows], textposition="outside", textfont_color="#e2e8f0"))
        fig.add_vline(x=50, line_dash="dash", line_color="#64748b", annotation_text="50% 平衡线")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(range=[35, 65], gridcolor="#1e293b"),
                          yaxis=dict(autorange="reversed", gridcolor="#1e293b"), height=340)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    allrows = sorted(maps_data.items(), key=lambda x: x[1]["total_games"], reverse=True)
    html = '<div class="sc-card"><table class="allmap-table"><thead><tr>' \
           '<th>#</th><th>地图名</th><th>场次</th><th>Z 胜率</th><th>P 胜率</th><th>T 胜率</th><th>平衡度</th></tr></thead><tbody>'
    for i, (name, d) in enumerate(allrows, 1):
        zw, pw, tw = d["zerg"]["winrate"], d["protoss"]["winrate"], d["terran"]["winrate"]
        diff = max(zw, pw, tw) - min(zw, pw, tw)
        dcls = "good" if diff <= 5 else "warn" if diff <= 10 else "mid" if diff <= 15 else "bad"
        dtxt = "平衡" if diff <= 5 else "较平衡" if diff <= 10 else "略失衡" if diff <= 15 else "失衡"
        html += f'<tr><td>{i}</td><td>{name}</td><td>{d["total_games"]:,}</td>' \
                f'<td class="{wr_cls(zw)}">{zw:.1f}%</td><td class="{wr_cls(pw)}">{pw:.1f}%</td>' \
                f'<td class="{wr_cls(tw)}">{tw:.1f}%</td><td><span class="dot {dcls}"></span>{dtxt}</td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

st.markdown('<p style="text-align:center;color:#475569;margin-top:2rem;">⚔️ SC:BW Map Stats · Data from eloboard.com</p>',
            unsafe_allow_html=True)