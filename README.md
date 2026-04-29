# 电商运营 Agent 项目

这是一个可运行的电商运营多 Agent MVP，用来完成：

- 商品资料整理
- 竞品分析
- 用户评价洞察
- 标题/详情页文案生成
- 短视频脚本生成
- 客服 FAQ 生成
- A/B 测试和转化复盘计划
- 合规风险检查

项目默认支持两种模式：

1. **有 OpenAI API Key**：调用模型生成更高质量内容。
2. **无 API Key**：使用内置 fallback 规则生成可演示结果，方便面试、申请或本地测试。

## 目录结构

```text
ecommerce_agent_project/
  app/main.py                 # FastAPI 接口
  data/                       # 示例数据
  outputs/                    # 生成结果
  src/ecom_agent/
    agents.py                 # 各个专业 Agent
    cli.py                    # 命令行入口
    io_utils.py               # 文件读写与 Markdown 渲染
    llm.py                    # OpenAI Responses API 封装
    models.py                 # 数据结构
    orchestrator.py           # 多 Agent 编排
    text_utils.py             # 关键词、价格、指标等工具
  run.py                      # 本地 CLI 启动脚本
  requirements.txt
  .env.example
```

## 快速开始

```bash
cd ecommerce_agent_project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 方式一：无 API Key 演示

```bash
python run.py \
  --product data/product.json \
  --competitors data/competitors.csv \
  --reviews data/reviews.csv \
  --metrics data/metrics.csv \
  --out outputs \
  --no-llm
```

### 方式二：调用 OpenAI API

```bash
cp .env.example .env
# 编辑 .env，填写 OPENAI_API_KEY
python run.py \
  --product data/product.json \
  --competitors data/competitors.csv \
  --reviews data/reviews.csv \
  --metrics data/metrics.csv \
  --out outputs
```

生成后会在 `outputs/时间-商品名/` 下得到：

- `campaign.json`
- `campaign.md`

## 启动 API 服务

```bash
uvicorn app.main:app --reload
```

测试：

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d @data/api_payload_example.json
```

你也可以打开浏览器访问：

```text
http://127.0.0.1:8000/docs
```

## 输入数据格式

### product.json

```json
{
  "name": "商品名",
  "brand": "品牌",
  "category": "类目",
  "price": "价格",
  "target_user": "目标用户",
  "pain_points": ["痛点"],
  "selling_points": ["卖点"],
  "specs": {"规格名": "规格值"},
  "tone": "语气风格",
  "platform": "平台",
  "keywords": ["关键词"],
  "constraints": ["合规限制"]
}
```

### competitors.csv

```csv
title,price,rating,sales,review_summary,url
竞品标题,99,4.8,1000+,评价摘要,https://example.com
```

### reviews.csv

```csv
content,rating,source
用户评价,5,own_store
```

### metrics.csv

```csv
variant_id,title,exposure,clicks,conversions,revenue,spend
A,标题A,1000,80,10,990,200
```

## 适合继续扩展的方向

- 接入电商平台官方 API，定时同步商品、订单和客服问题。
- 增加向量知识库，把历史爆款文案、客服话术、品牌规范做成检索上下文。
- 增加多 Agent 评审：文案 Agent、合规 Agent、投放 Agent 互相打分。
- 加入自动任务流：每天读取转化数据，自动生成下一轮标题和脚本。
- 接入看板，把 CTR、CVR、ROAS 和内容版本关联起来。

## 合规提醒

本项目不会绕过登录、验证码、付费墙或平台限制。竞品数据建议通过平台允许的方式获得，例如官方 API、商家后台导出、手动整理、公开授权数据源。
