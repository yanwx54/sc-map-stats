# ⚔️ SC:BW 地图数据统计工具

实时抓取 [eloboard.com](http://eloboard.com/men/bbs/board.php?bo_table=map_stac) 的星际争霸:母巢之战地图对战数据，提供种族胜率、平衡性评分、历史趋势等可视化分析。

🔗 **在线访问**：https://yanwx54-sc-map-stats.streamlit.app

## ✨ 功能
- 📊 当前赛季地图种族胜率详情 + 雷达图
- ⚔️ 种族对抗总览（ZvT/ZvP/PvT...）
- 🗺️ 全部地图排名 + 胜率热力图
- 🆚 多地图平衡性对比
- 📈 历史胜率趋势（GitHub Actions 每日自动采集）
- 🎯 平衡性评分系统（0-100 分）
- 🌐 中/英双语
- 📥 数据导出 CSV

## 🛠️ 技术栈
Streamlit · Plotly · BeautifulSoup · GitHub Actions

## 🔄 换赛季
只需编辑 `season.json`，无需改代码。

## 🧪 测试
```bash
pip install pytest
pytest tests/