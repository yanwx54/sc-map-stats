# ⚔️ StarCraft: Brood War 地图数据统计

一个基于 Streamlit 的星际争霸：母巢之战地图平衡性数据展示应用。

## 📋 项目简介

本项目从 [eloboard.com](http://eloboard.com/) 抓取星际争霸职业比赛地图数据，分析并展示各地图的种族胜率、对战详情等平衡性统计数据。

## ✨ 功能特性

- **实时数据抓取**：自动从 eloboard 获取最新比赛数据
- **地图平衡性分析**：展示每张地图的种族胜率差异和平衡性评级
- **赛季地图池**：支持显示当前赛季所有地图的详细统计
- **种族对抗总览**：汇总所有地图的种族对抗数据（ZvT, ZvP, PvT 等）
- **全地图排名**：按平衡性对所有收录地图进行排序
- **电竞风格 UI**：深色主题，可视化进度条，响应式设计

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动（默认端口）。

## 📁 项目结构

```
.
├── app.py              # 主应用程序
├── requirements.txt    # Python 依赖
├── .streamlit/         # Streamlit 配置
└── README.md          # 项目说明文档
```

## 🗺️ 当前赛季地图池

| 玩家数 | 韩文名 | 英文名 | 版本 |
|--------|--------|--------|------|
| 2 | 오디세이 | Odyssey | RE 2.0 |
| 2 | 컬러리스 페이트 | Colorless Fate | 1.1 |
| 3 | 아이올로스 | Aiolos | 1.0b |
| 4 | 녹아웃 | KnockOut | 1.4 |
| 4 | 백 룸 | Backrooms | 1.0 |
| 4 | 애티튜드 | Attitude | SE 2.1 |
| 4 | 옥타곤 | Octagon | SE 2.0 |

## 📊 数据来源

- 数据源：[eloboard.com/map_stac](http://eloboard.com/men/bbs/board.php?bo_table=map_stac)
- 数据每小时自动刷新一次
- 可点击"🔄 立即刷新数据"按钮手动刷新

## 🎨 平衡性评级标准

| 评级 | 胜率差 | 说明 |
|------|--------|------|
| 🟢 非常平衡 | ≤ 5% | 三族胜率非常接近 |
| 🟡 较为平衡 | ≤ 10% | 存在轻微优势种族 |
| 🟠 略有失衡 | ≤ 15% | 明显优势/劣势种族 |
| 🔴 明显失衡 | > 15% | 严重不平衡 |

## 🛠️ 技术栈

- **前端**: Streamlit, Plotly, 自定义 CSS
- **数据抓取**: requests, BeautifulSoup4
- **数据处理**: pandas
- **可视化**: Plotly Graph Objects

## 📝 注意事项

1. 本应用仅用于数据展示，不存储任何用户数据
2. 数据完全来源于公开的 eloboard 网站
3. 如遇数据加载失败，可能是目标网站临时不可用，请点击刷新按钮重试

## 📄 License

MIT License

---

**作者**: Auto-generated  
**最后更新**: 2024
