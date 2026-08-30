# Claim2Value 数据源与配置清单

> 整理时间：2026-08-29
> 用途：为 Claim2Value Agent 选择可获取的数据源、API、模型配置

---

## 一、金融与市场数据

### 1.1 A 股数据（机器人/工业上市公司）

| 数据源 | 费用 | 覆盖 | 用法 | 备注 |
|---|---|---|---|---|
| **AKShare** | 免费开源 | A 股历史行情、财务指标、基本面 | `ak.stock_zh_a_hist()` | 推荐主力免费源；字段可能随版本变化，需 pin 版本 |
| **Tushare Pro** | 基础免费/高级付费 | A 股、港股、基本面、宏观 | `tushare.pro_api(token)` | 需要 token；基本面数据较全 |
| **Baostock** | 免费 | A 股历史数据 | - | 备选 |
| **YFinance** | 免费 | 美股/港股/全球 | `yfinance.download()` | 中国大陆访问不稳定 |
| **FMP (Financial Modeling Prep)** | 250 req/day 免费 | 美股财报 | - | A 股覆盖不全 |
| **OpenBB + extensions** | 开源 | 统一接口 | `openbb-tushare`, `openbb-akshare` | 可减少多源拼接 |

**推荐组合：**
- A 股行情+基本面：**AKShare 为主，Tushare Pro 为辅**
- 美股/全球：**YFinance 或 FMP**

### 1.2 示例代码

```python
# AKShare A 股历史行情
import akshare as ak
df = ak.stock_zh_a_hist(
    symbol="688017",  # 绿的谐波
    period="daily",
    start_date="20240101",
    end_date="20260828",
    adjust="qfq"
)

# Tushare Pro 基本面
import tushare as ts
pro = ts.pro_api("YOUR_TOKEN")
fina = pro.fina_indicator(ts_code="688017.SH")
```

---

## 二、专利与技术资料数据

| 数据源 | 费用 | 覆盖 | 用法 | 备注 |
|---|---|---|---|---|
| **Google Patents** | 免费（网页） | 全球 1.2 亿+ 专利 | 网页搜索 | 无官方免费批量 API；BigQuery 有数据集 |
| **USPTO Open Data Portal** | 免费 API | 美国专利全文、file wrapper | REST API + key | Developer Hub 2026 年中迁移到 ODP |
| **PatentsView API** | 免费 | 美国专利结构化数据 | REST API | 适合批量查询 |
| **WIPO PATENTSCOPE** | 免费搜索/付费 API | PCT + 123 个国家 | 网页搜索 | 批量下载 prohibited；付费 SOAP API |
| **CNIPA** | 免费网页 | 中国专利 | 网页搜索 | 无官方免费批量 API；常见浏览器驱动适配 |
| **EPO Open Patent Services (OPS)** | 免费有限额 | EPO/WIPO 家族/法律状态 | REST API | 有 rate limit |
| **Lens.org** | 免费/付费 | 全球专利聚合 | 网页/API | 适合学术用途 |
| **patent-client-agents / Uni-CLI** | 开源 | 多源归一化 | GitHub | 可聚合 Google Patents/USPTO/EPO/WIPO/CNIPA |

**推荐组合：**
- 快速原型：**Google Patents 网页搜索 + 手动整理专利清单**
- 自动化：**patent-client-agents 或 USPTO PatentsView API**
- 中国专利：**CNIPA 网页 + 浏览器驱动（如 Playwright）**

---

## 三、行业与技术资料

| 数据源 | 类型 | 用途 |
|---|---|---|
| **公司公告/年报/招股书** | 官方 PDF | 产品参数、产能、客户、BOM |
| **产品 datasheet** | 厂商 PDF | torque density、weight、efficiency |
| **券商研报** | Wind/同花顺/东方财富 | 行业空间、竞争格局、盈利预测 |
| **行业研究报告** | IIM、高工机器人、OFweek | 市场规模、技术趋势 |
| **公司官网/公众号** | 公开信息 | 新品发布、产能扩张 |
| **Zhinno Robotics / CubeMars 技术博客** | 公开文章 | 扭矩密度对比、选型指南 |

**推荐垂直：**
- 人形/工业机器人关节：绿的谐波(688017)、来福谐波、步科股份、禾川科技、雷赛智能
- 功率半导体/SiC：士兰微、斯达半导、时代电气、比亚迪半导体
- 伺服电机/减速器：汇川技术、埃斯顿、双环传动、中大力德

---

## 四、LLM / 模型配置

### 4.1 推荐模型路由

| Agent 角色 | 推荐模型 | 理由 |
|---|---|---|
| **Master Planner / Critic** | GPT-4o / Claude 3.5 Sonnet | 强 reasoning、复杂规划 |
| **金融推理** | Ling-3.0-flash-Fin (如果免费额度可用) | 金融增强、长上下文 |
| **Claim Verification / 抽取** | DeepSeek-V3 / Qwen2.5 | 便宜、中文好 |
| **Engineering Analysis** | GPT-4o / Claude | 技术文档理解 |
| **Structured Output** | 建议固定 JSON Mode | 减少 schema 漂移 |

### 4.2 Ling-3.0-flash-Fin 当前状态

| 属性 | 信息 |
|---|---|
| 提供商 | InclusionAI / 蚂蚁百灵 |
| 总参数量 | 124 B |
| 激活参数量 | ~5.1 B |
| 上下文窗口 | 256K–262K tokens |
| 最大输出 | 32K tokens |
| 免费端点 | OpenRouter: `inclusionai/ling-3.0-flash-fin:free`；Vercel AI Gateway |
| 限时免费 | 2026-08-27 起约一个月 |
| 注意 | 免费端点可能限流；避免发送敏感数据；正式比赛前需确认是否仍免费 |

**OpenRouter 调用示例：**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OPENROUTER_API_KEY"
)

response = client.chat.completions.create(
    model="inclusionai/ling-3.0-flash-fin:free",
    messages=[{"role": "user", "content": "分析绿的谐波2025年关节模组扭矩密度提升对毛利率的影响..."}]
)
```

### 4.3 备选模型端点

| 平台 | 模型 | 备注 |
|---|---|---|
| OpenRouter | GPT-4o-mini, Claude 3.5 Haiku, DeepSeek-V3 | 统一 OpenAI-compatible API |
| 硅基流动 /  together.ai | Qwen, DeepSeek | 国内/海外备选 |
| Anthropic API | Claude 3.5 Sonnet | 稳定，稍贵 |
| OpenAI API | GPT-4o / GPT-4o-mini | 稳定 |

---

## 五、技术栈配置

### 5.1 推荐技术栈

| 层级 | 工具 |
|---|---|
| Agent 框架 | **LangGraph**（状态机清晰，适合 verification loop） |
| LLM 调用 | OpenAI SDK + OpenRouter 统一端点 |
| RAG / 向量库 | LangChain + **Chroma**（轻量）或 Milvus |
| 财务模型 | Python + **openpyxl**（快速）或借鉴 ModelForge 思想 |
| 前端 Demo | **Streamlit** 或 Gradio（2 周最快） |
| 数据缓存 | SQLite / JSON files |
| 部署 | 本地运行即可（比赛 Demo） |

### 5.2 Python 环境

```bash
conda create -n claim2value python=3.11
conda activate claim2value
pip install langchain langgraph openai akshare tushare openpyxl streamlit pandas numpy
```

---

## 六、真实案例数据候选

### 案例 1：绿的谐波（688017）
- 2025 世界机器人大会发布人形机器人专用谐波减速器
- 扭矩密度行业从 4.5 → 6.2 Nm/kg
- 已进入天工、智元、据传特斯拉 Optimus 供应链
- 年产能数十万套

### 案例 2：步科股份
- 第四代 FMK 无框力矩电机功率密度提升 20%
- 扭矩覆盖 0.11–9.2 Nm
- 2026 Q1 人形机器人用电机销量 3.5 万台，同比 +246%
- 进入 ABB、KUKA 供应链

### 案例 3：禾川科技
- 高功率密度无框力矩电机扭矩密度 4.5 Nm/kg
- 体积缩小 30%
- 2025 年小批量订单，2026 年批量交付
- 与优必选、天工合作

**推荐首选案例：绿的谐波**
- 数据最丰富
- 上市公司，财务数据完整
- 市场关注度高
- 技术参数公开

---

## 七、数据采集清单（针对绿的谐波案例）

| 数据类型 | 来源 | 优先级 |
|---|---|---|
| 公司公告/年报 | CNINFO 巨潮资讯网 | 高 |
| 股价/财务指标 | AKShare / Tushare | 高 |
| 产品 datasheet | 公司官网、展会资料 | 高 |
| 专利 | Google Patents / CNIPA | 中 |
| 竞争对手参数 | 来福谐波、Harmonic Drive、Nidec 等 | 中 |
| 券商研报 | Wind / 同花顺 / 东方财富 | 中 |
| 行业报告 | IIM、高工机器人 | 低 |

---

## 八、数据风险与应对

| 风险 | 应对 |
|---|---|
| AKShare 字段/接口变化 | pin 版本 + 做 schema 校验 |
| Tushare token 权限不足 | 用免费基础版，避免依赖高级字段 |
| 专利数据获取不稳定 | 手工准备 5–10 个核心专利作为 benchmark |
| 公司参数口径不一致 | 在 Claim Verification 层显式标注 definition mismatch |
| LLM 免费额度到期 | 准备 DeepSeek/Qwen 作为备选 |
| 网络访问限制 | 所有外部 API 加 try/except + fallback |

---

## 九、建议的本地数据目录

```
research_materials/data/
├── raw/
│   ├── company_filings/      # 年报/公告 PDF
│   ├── datasheets/           # 产品 datasheet PDF
│   ├── patents/              # 专利文本/PDF
│   ├── analyst_reports/      # 研报
│   └── industry_reports/     # 行业报告
├── processed/
│   ├── claim_bank.json       # 测试用 claim 集合
│   ├── parameter_table.csv   # 技术参数对比表
│   ├── bom_template.csv      # BOM 模板
│   └── financial_model.xlsx  # 财务模型模板
└── benchmark/
    ├── claim_verification.json
    ├── engineering_accuracy.json
    ├── economic_reasoning.json
    └── financial_accuracy.json
```
