import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, io, base64
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scraper

# ============================================================
# 多语言
# ============================================================
LANG = {
    "中文": {
        "title": "⚔️ StarCraft: Brood War 地图数据统计",
        "source": "数据来源 eloboard.com · 更新于",
        "refresh": "🔄 立即刷新数据",
        "tab1": "📊 赛季地图详情", "tab2": "⚔️ 种族对抗总览", "tab3": "🗺️ 全部地图排名",
        "tab4": "🆚 地图对比", "tab5": "📈 历史趋势",
        "total_maps": "收录地图", "season_games": "赛季总场次", "best": "最平衡", "worst": "最失衡",
        "matchup": "对战详情", "games": "总场次", "balance": "平衡性", "score": "平衡分",
        "filter": "自定义地图池", "lang": "语言", "export": "📥 导出当前数据 (CSV)",
    },
    "EN": {
        "title": "⚔️ StarCraft: Brood War Map Stats",
        "source": "Data from eloboard.com · Updated",
        "refresh": "🔄 Refresh Data",
        "tab1": "📊 Season Maps", "tab2": "⚔️ Matchup Overview", "tab3": "🗺️ All Maps Ranking",
        "tab4": "🆚 Compare Maps", "tab5": "📈 History Trend",
        "total_maps": "Maps", "season_games": "Season Games", "best": "Most Balanced", "worst": "Least Balanced",
        "matchup": "Matchups", "games": "Total Games", "balance": "Balance", "score": "Score",
        "filter": "Custom Map Pool", "lang": "Language", "export": "📥 Export CSV",
    },
}

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="SC:BW Map Stats", page_icon="⚔️", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
  .stApp{background:radial-gradient(1200px 600px at 50% -10%,#1e3a8a33,transparent),#0f172a;}
  #MainMenu,footer{visibility:hidden;}
  .block-container{padding-top:1rem;max-width:1200px;}
  .hero{position:relative;height:230px;border-radius:20px;overflow:hidden;margin-bottom:1.2rem;
        background:linear-gradient(135deg,#1e3a8a,#312e81 50%,#0f172a);border:1px solid #334155;
        box-shadow:0 20px 50px -20px #000a;}
  .hero-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;opacity:.88;}
  .hero-text{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;
        justify-content:center;align-items:center;text-align:center;padding:1rem 2rem;
        background:linear-gradient(180deg,rgba(15,23,42,.10) 0%,rgba(15,23,42,.35) 55%,rgba(15,23,42,.65) 100%);}
  .hero-text h1{margin:0;font-size:2rem;font-weight:800;
        background:linear-gradient(90deg,#4ade80,#60a5fa,#f87171);
        -webkit-background-clip:text;background-clip:text;color:transparent;
        filter:drop-shadow(0 2px 8px rgba(0,0,0,.85));}
  .hero-text p{margin:.4rem 0 0;color:#f1f5f9;font-size:.95rem;text-shadow:0 1px 5px rgba(0,0,0,.9);}
  .hero-nobg{height:auto;}
  .hero-nobg .hero-text{height:auto;padding:2.5rem 2rem;background:none;}
  .metric-row{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.4rem;}
  .metric-card{background:rgba(30,41,59,.6);border:1px solid rgba(148,163,184,.15);
        border-radius:14px;padding:1rem;text-align:center;}
  .mc-label{color:#94a3b8;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;}
  .mc-value{font-size:1.8rem;font-weight:800;margin:.3rem 0;color:#f1f5f9;}
  .mc-value.high{color:#4ade80;}.mc-value.low{color:#f87171;}.mc-value.blue{color:#60a5fa;}
  .mc-sub{color:#64748b;font-size:.78rem;}
  .sc-card{background:rgba(30,41,59,.55);backdrop-filter:blur(10px);
        border:1px solid rgba(148,163,184,.15);border-radius:16px;padding:1.3rem 1.5rem;margin-bottom:1.2rem;}
  .map-head{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;margin-bottom:.9rem;}
  .map-players{background:#334155;color:#cbd5e1;font-size:.75rem;font-weight:700;padding:.2rem .6rem;border-radius:6px;}
  .map-title{font-size:1.25rem;font-weight:700;color:#f1f5f9;flex:1;}
  .map-en{color:#60a5fa;font-weight:500;font-size:1rem;}
  .map-ver{color:#64748b;font-size:.85rem;}
  .bal-badge{font-size:.78rem;font-weight:700;padding:.3rem .7rem;border-radius:20px;}
  .bal-good{background:#22c55e22;color:#4ade80;border:1px solid #22c55e55;}
  .bal-warn{background:#fbbf2422;color:#fbbf24;border:1px solid #fbbf2455;}
  .bal-mid{background:#f9731622;color:#fb923c;border:1px solid #f9731655;}
  .bal-bad{background:#ef444422;color:#f87171;border:1px solid #ef444455;}
  .bal-nodata{background:#64748b22;color:#94a3b8;border:1px solid #64748b55;}
  .race-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.9rem;}
  .race-box{border-radius:12px;padding:.9rem 1rem;border:1px solid;}
  .race-box.zerg{background:#4ade8010;border-color:#4ade8033;}
  .race-box.protoss{background:#60a5fa10;border-color:#60a5fa33;}
  .race-box.terran{background:#f8717110;border-color:#f8717133;}
  .rb-label{font-size:.85rem;font-weight:600;color:#cbd5e1;}
  .rb-wr{font-size:1.8rem;font-weight:800;margin:.2rem 0;}
  .rb-wl{font-size:.8rem;color:#94a3b8;margin-bottom:.5rem;}
  .bar-track{width:100%;height:8px;background:rgba(255,255,255,.08);border-radius:99px;overflow:hidden;}
  .bar-fill{height:100%;border-radius:99px;}
  .bar-fill.high{background:linear-gradient(90deg,#22c55e,#4ade80);}
  .bar-fill.low{background:linear-gradient(90deg,#f97316,#fbbf24);}
  .high{color:#4ade80;}.low{color:#fb923c;}
  .mu-title{margin:1.2rem 0 .6rem;color:#94a3b8;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;}
  .matchup-list{display:grid;grid-template-columns:repeat(2,1fr);gap:.5rem 1.5rem;}
  .mu-row{display:flex;align-items:center;gap:.7rem;}
  .mu-label{width:42px;font-weight:700;color:#cbd5e1;}
  .mu-track{flex:1;}
  .mu-wr{width:52px;text-align:right;font-weight:700;}
  .mu-wl{width:80px;text-align:right;color:#64748b;font-size:.8rem;}
  .allmap-table{width:100%;border-collapse:collapse;}
  .allmap-table th{text-align:left;color:#94a3b8;font-size:.78rem;text-transform:uppercase;padding:.7rem .8rem;border-bottom:2px solid #334155;}
  .allmap-table td{padding:.8rem;border-bottom:1px solid #1e293b;color:#e2e8f0;}
  .allmap-table tr:hover td{background:rgba(255,255,255,.03);}
  .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:.4rem;}
  .dot.good{background:#4ade80;}.dot.warn{background:#fbbf24;}.dot.mid{background:#fb923c;}.dot.bad{background:#f87171;}.dot.nodata{background:#64748b;}
  @media(max-width:768px){.hero{height:170px;}.hero-text h1{font-size:1.4rem;}.metric-row{grid-template-columns:repeat(2,1fr);}.race-grid{grid-template-columns:1fr;}.matchup-list{grid-template-columns:1fr;}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================
# 侧边栏：语言 + 自定义地图池
# ============================================================
season = scraper.load_season()
all_map_names = [m["english"] for m in season["maps"]]

with st.sidebar:
    lang = st.selectbox(LANG["中文"]["lang"], ["中文", "EN"], key="lang_sel")
    st.markdown(f"#### {LANG['中文']['filter']}")
    selected = st.multiselect("选择要显示的地图", all_map_names, default=all_map_names, key="map_pool")

T = LANG[lang]
season_maps = [m for m in season["maps"] if m["english"] in selected]

# ============================================================
# 横幅 base64 内联（让图片与文字在同一容器，可叠加+可控高度）
# ============================================================
BANNER_B64 = None
if os.path.exists("banner.png"):
    with open("banner.png", "rb") as _f:
        BANNER_B64 = base64.b64encode(_f.read()).decode()

_now = datetime.now().strftime("%Y-%m-%d %H:%M")
if BANNER_B64:
    hero_html = (
        '<div class="hero">'
        f'<img class="hero-bg" src="data:image/png;base64,{BANNER_B64}" alt="banner">'
        f'<div class="hero-text"><h1>{T["title"]}</h1>'
        f'<p>{T["source"]} {_now} · {season["season_name"]}</p></div></div>'
    )
else:
    hero_html = (
        '<div class="hero hero-nobg"><div class="hero-text">'
        f'<h1>{T["title"]}</h1><p>{T["source"]} {_now} · {season["season_name"]}</p></div></div>'
    )
st.markdown(hero_html, unsafe_allow_html=True)

# ============================================================
# 数据获取函数（必须先定义，按钮才能调用）
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def scrape_cached():
    return scraper.scrape(retries=3)

if st.button(T["refresh"], type="primary", key="refresh_btn"):
    scrape_cached.clear()
    st.rerun()

maps_data, status = scrape_cached()

if status == "network":
    st.error("❌ 无法连接 eloboard（网络或反爬限制）。请稍后点击刷新重试。")
    st.stop()
elif status == "structure":
    st.error("⚠️ 数据解析失败：eloboard 网页结构可能已改版，请联系维护者更新解析逻辑。")
    st.stop()

# ============================================================
# 导出图片辅助函数（英文标签，避免云端中文乱码）
# ============================================================
def _en_balance(sc):
    if sc is None: return "N/A"
    if sc >= 80: return "Balanced"
    if sc >= 60: return "Fair"
    if sc >= 40: return "Skewed"
    return "Broken"

def build_summary_image(maps_data, season_maps):
    rows = []
    for mi in season_maps:
        _, md = scraper.find_map_data(mi, maps_data)
        if md and md["total_games"] > 0:
            z = md["zerg"]["winrate"]; p = md["protoss"]["winrate"]; t = md["terran"]["winrate"]
            sc = scraper.balance_score(z, p, t, md["total_games"])
            rows.append([mi["english"], f'{md["total_games"]:,}', f"{z:.1f}", f"{p:.1f}", f"{t:.1f}",
                         f"{sc}" if sc is not None else "-", _en_balance(sc)])
    if not rows:
        return None
    cols = ["Map", "Games", "Z%", "P%", "T%", "Score", "Balance"]
    n = len(rows)
    fig, ax = plt.subplots(figsize=(11, 0.55 * n + 1.6))
    fig.patch.set_facecolor("#0f172a"); ax.set_facecolor("#0f172a"); ax.axis("off")
    ax.set_title("SC:BW  ·  Season Map Stats", color="#f1f5f9", fontsize=20, fontweight="bold", pad=26)
    ax.text(0.5, 1.03, f"Source: eloboard.com  |  {datetime.now().strftime('%Y-%m-%d')}",
            transform=ax.transAxes, ha="center", color="#94a3b8", fontsize=10)
    tbl = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(11); tbl.scale(1, 1.7)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#334155")
        if r == 0:
            cell.set_facecolor("#334155"); cell.get_text().set_color("#e2e8f0"); cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor("#1e293b"); cell.get_text().set_color("#e2e8f0")
            if c in (2, 3, 4):
                try:
                    v = float(rows[r - 1][c])
                    cell.get_text().set_color("#4ade80" if v >= 50 else "#fb923c")
                    cell.get_text().set_fontweight("bold")
                except Exception:
                    pass
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

# ============================================================
# 顶部数据看板
# ============================================================
season_games, best, worst = 0, None, None
for mi in season_maps:
    _, md = scraper.find_map_data(mi, maps_data)
    if md and md["total_games"] > 0:
        season_games += md["total_games"]
        sc = scraper.balance_score(md["zerg"]["winrate"], md["protoss"]["winrate"],
                                   md["terran"]["winrate"], md["total_games"])
        if sc is not None:
            if best is None or sc > best[1]:  best = (mi["english"], sc)
            if worst is None or sc < worst[1]: worst = (mi["english"], sc)

def metric(label, value, sub, vcls=""):
    return f'<div class="metric-card"><div class="mc-label">{label}</div>' \
           f'<div class="mc-value {vcls}">{value}</div><div class="mc-sub">{sub}</div></div>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(metric(T["total_maps"], len(maps_data), "eloboard 全站", "blue"), unsafe_allow_html=True)
c2.markdown(metric(T["season_games"], f"{season_games:,}", season["season_name"], "blue"), unsafe_allow_html=True)
c3.markdown(metric(T["best"], best[0] if best else "-", f"{T['score']} {best[1]}" if best else "", "high"), unsafe_allow_html=True)
c4.markdown(metric(T["worst"], worst[0] if worst else "-", f"{T['score']} {worst[1]}" if worst else "", "low"), unsafe_allow_html=True)

# 导出 CSV + 导出图片（两列并排）
export_rows = []
for name, d in maps_data.items():
    export_rows.append({"地图": name, "场次": d["total_games"],
                        "Z胜率": d["zerg"]["winrate"], "P胜率": d["protoss"]["winrate"], "T胜率": d["terran"]["winrate"]})
csv = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8-sig")
ec1, ec2 = st.columns(2)
ec1.download_button(T["export"], csv, "sc_map_stats.csv", "text/csv", key="export_csv")
png_bytes = build_summary_image(maps_data, season_maps)
if png_bytes:
    ec2.download_button("🖼️ 导出为图片 (PNG)", png_bytes, "sc_map_stats.png", "image/png", key="export_png")

# ============================================================
# Tabs
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([T["tab1"], T["tab2"], T["tab3"], T["tab4"], T["tab5"]])

RACE = {"zerg": ("Zerg", "zerg"), "protoss": ("Protoss", "protoss"), "terran": ("Terran", "terran")}

def wr_cls(wr): return "high" if wr >= 50 else "low"

# ---- Tab1 赛季详情（无雷达图）----
with tab1:
    for mi in season_maps:
        fn, md = scraper.find_map_data(mi, maps_data)
        head = f'<div class="map-head"><span class="map-players">{mi["players"]}人图</span>' \
               f'<span class="map-title">{mi["korean"]} <span class="map-en">{mi["english"]}</span> ' \
               f'<span class="map-ver">{mi["version"]}</span></span>'
        if md and md["total_games"] > 0:
            z, p, t = md["zerg"], md["protoss"], md["terran"]
            sc = scraper.balance_score(z["winrate"], p["winrate"], t["winrate"], md["total_games"])
            bcls, btxt = scraper.balance_label(sc)
            sc_txt = f"{sc}" if sc is not None else "—"
            head += f'<span class="bal-badge bal-{bcls}">{btxt} · {T["score"]} {sc_txt}</span></div>'
            body = f'<div style="color:#94a3b8;margin-bottom:1rem;">{T["games"]} <b style="color:#f1f5f9;font-size:1.1rem;">{md["total_games"]:,}</b></div>'
            body += '<div class="race-grid">'
            for key, (rname, rcls) in RACE.items():
                d = md[key]
                body += f'<div class="race-box {rcls}"><div class="rb-label">{rname}</div>' \
                        f'<div class="rb-wr {wr_cls(d["winrate"])}">{d["winrate"]:.1f}%</div>' \
                        f'<div class="rb-wl">{d["wins"]:,} 胜 / {d["losses"]:,} 负</div>' \
                        f'<div class="bar-track"><div class="bar-fill {wr_cls(d["winrate"])}" style="width:{d["winrate"]:.1f}%"></div></div></div>'
            body += '</div>'
            if md["matchups"]:
                body += f'<div class="mu-title">{T["matchup"]}</div><div class="matchup-list">'
                for k in ["ZvT", "ZvP", "PvZ", "PvT", "TvZ", "TvP"]:
                    if k in md["matchups"]:
                        d = md["matchups"][k]
                        body += f'<div class="mu-row"><span class="mu-label">{k}</span>' \
                                f'<div class="bar-track mu-track"><div class="bar-fill {wr_cls(d["winrate"])}" style="width:{d["winrate"]:.1f}%"></div></div>' \
                                f'<span class="mu-wr {wr_cls(d["winrate"])}">{d["winrate"]:.1f}%</span>' \
                                f'<span class="mu-wl">{d["wins"]:,}-{d["losses"]:,}</span></div>'
                body += '</div>'
            st.markdown(f'<div class="sc-card">{head}{body}</div>', unsafe_allow_html=True)
        else:
            head += '<span class="bal-badge bal-nodata">暂无数据</span></div>'
            st.markdown(f'<div class="sc-card">{head}<div style="color:#94a3b8;text-align:center;padding:1rem;">⚠️ 该地图尚未被 eloboard 收录</div></div>',
                        unsafe_allow_html=True)

# ---- Tab2 种族总览 ----
with tab2:
    totals = {}
    for mi in season_maps:
        _, md = scraper.find_map_data(mi, maps_data)
        if md:
            for k, v in md.get("matchups", {}).items():
                totals.setdefault(k, {"wins": 0, "losses": 0})
                totals[k]["wins"] += v["wins"]; totals[k]["losses"] += v["losses"]
    rows = []
    for k in ["ZvT", "ZvP", "PvZ", "PvT", "TvZ", "TvP"]:
        if k in totals:
            d = totals[k]; tot = d["wins"] + d["losses"]
            wr = round(d["wins"] / tot * 100, 1) if tot else 0
            rows.append({"matchup": k, "wins": d["wins"], "losses": d["losses"], "wr": wr})
    html = '<div class="sc-card">'
    for r in rows:
        html += f'<div class="mu-row" style="margin-bottom:.7rem;">' \
                f'<span class="mu-label" style="width:54px;font-size:1.05rem;">{r["matchup"]}</span>' \
                f'<div class="bar-track mu-track" style="height:12px;"><div class="bar-fill {wr_cls(r["wr"])}" style="width:{r["wr"]}%"></div></div>' \
                f'<span class="mu-wr {wr_cls(r["wr"])}" style="width:60px;font-size:1.05rem;">{r["wr"]}%</span>' \
                f'<span class="mu-wl" style="width:110px;">{r["wins"]:,} - {r["losses"]:,}</span></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    if rows:
        fig = go.Figure(go.Bar(
            y=[r["matchup"] for r in rows], x=[r["wr"] for r in rows], orientation="h",
            marker_color=["#4ade80" if r["wr"] >= 50 else "#fb923c" for r in rows],
            text=[f'{r["wr"]}%' for r in rows], textposition="outside", textfont_color="#e2e8f0"))
        fig.add_vline(x=50, line_dash="dash", line_color="#64748b", annotation_text="50%")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(range=[35, 65], gridcolor="#1e293b"),
                          yaxis=dict(autorange="reversed", gridcolor="#1e293b"), height=340)
        st.plotly_chart(fig, use_container_width=True, key="matchup_bar")

# ---- Tab3 全部地图（热力图）----
with tab3:
    allrows = sorted(maps_data.items(), key=lambda x: x[1]["total_games"], reverse=True)
    html = '<div class="sc-card"><table class="allmap-table"><thead><tr>' \
           '<th>#</th><th>地图名</th><th>场次</th><th>Z</th><th>P</th><th>T</th><th>平衡分</th><th>平衡度</th></tr></thead><tbody>'
    for i, (name, d) in enumerate(allrows, 1):
        zw, pw, tw = d["zerg"]["winrate"], d["protoss"]["winrate"], d["terran"]["winrate"]
        sc = scraper.balance_score(zw, pw, tw, d["total_games"])
        bcls, btxt = scraper.balance_label(sc)
        sc_txt = f"{sc}" if sc is not None else "—"
        html += f'<tr><td>{i}</td><td>{name}</td><td>{d["total_games"]:,}</td>' \
                f'<td class="{wr_cls(zw)}">{zw:.1f}%</td><td class="{wr_cls(pw)}">{pw:.1f}%</td>' \
                f'<td class="{wr_cls(tw)}">{tw:.1f}%</td><td>{sc_txt}</td>' \
                f'<td><span class="dot {bcls}"></span>{btxt}</td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)
    if allrows:
        names = [n for n, _ in allrows]
        zmat = [[d["zerg"]["winrate"], d["protoss"]["winrate"], d["terran"]["winrate"]] for _, d in allrows]
        fig = go.Figure(go.Heatmap(z=zmat, x=["Zerg", "Protoss", "Terran"], y=names,
                                   colorscale="RdYlGn", zmin=30, zmax=70,
                                   text=[[f"{v:.1f}%" for v in row] for row in zmat], texttemplate="%{text}"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"), height=420)
        st.plotly_chart(fig, use_container_width=True, key="heatmap")

# ---- Tab4 地图对比（分组柱状图）----
with tab4:
    opts = [m["english"] for m in season_maps]
    pick = st.multiselect("选择 2~3 张地图对比", opts, default=opts[:2] if len(opts) >= 2 else opts, key="cmp_pick")
    if len(pick) >= 2:
        cmp_rows = []
        for en in pick:
            mi = next(m for m in season_maps if m["english"] == en)
            _, md = scraper.find_map_data(mi, maps_data)
            if md and md["total_games"] > 0:
                sc = scraper.balance_score(md["zerg"]["winrate"], md["protoss"]["winrate"],
                                           md["terran"]["winrate"], md["total_games"])
                cmp_rows.append({"地图": en, "场次": md["total_games"], "Z胜率": md["zerg"]["winrate"],
                                 "P胜率": md["protoss"]["winrate"], "T胜率": md["terran"]["winrate"],
                                 "平衡分": sc if sc else 0})
        if cmp_rows:
            st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Zerg", x=[r["地图"] for r in cmp_rows], y=[r["Z胜率"] for r in cmp_rows], marker_color="#4ade80"))
            fig.add_trace(go.Bar(name="Protoss", x=[r["地图"] for r in cmp_rows], y=[r["P胜率"] for r in cmp_rows], marker_color="#60a5fa"))
            fig.add_trace(go.Bar(name="Terran", x=[r["地图"] for r in cmp_rows], y=[r["T胜率"] for r in cmp_rows], marker_color="#f87171"))
            fig.add_hline(y=50, line_dash="dash", line_color="#64748b", annotation_text="50%")
            fig.update_layout(barmode="group", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              yaxis=dict(range=[30, 70], gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"),
                              height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True, key="cmp_bar")
    else:
        st.info("请至少选择 2 张地图进行对比")

# ---- Tab5 历史趋势 ----
with tab5:
    history = scraper.load_history()
    if len(history) < 2:
        st.info("📈 历史数据由 GitHub Actions 每日自动采集。数据积累 2 天后即可在此查看胜率趋势。")
    else:
        en_opts = [m["english"] for m in season_maps]
        pick = st.selectbox("选择地图查看趋势", en_opts, key="trend_pick")
        dates, zs, ps, ts = [], [], [], []
        for h in history:
            if pick in h["maps"]:
                dates.append(h["date"])
                zs.append(h["maps"][pick]["z"]); ps.append(h["maps"][pick]["p"]); ts.append(h["maps"][pick]["t"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=zs, name="Zerg", line=dict(color="#4ade80")))
        fig.add_trace(go.Scatter(x=dates, y=ps, name="Protoss", line=dict(color="#60a5fa")))
        fig.add_trace(go.Scatter(x=dates, y=ts, name="Terran", line=dict(color="#f87171")))
        fig.add_hline(y=50, line_dash="dash", line_color="#64748b")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(range=[30, 70], gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"),
                          height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, key="trend_line")

st.markdown('<p style="text-align:center;color:#475569;margin-top:2rem;">⚔️ SC:BW Map Stats · Data from eloboard.com</p>',
            unsafe_allow_html=True)