from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import CampaignOutput, CompetitorItem, MetricsRow, PipelineInput, ProductInput, ReviewItem


ROOT = Path(__file__).resolve().parents[2]


def read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_csv_rows(path: Optional[str | Path]) -> List[Dict[str, Any]]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def load_pipeline_input(
    product_path: str | Path,
    competitors_path: Optional[str | Path] = None,
    reviews_path: Optional[str | Path] = None,
    metrics_path: Optional[str | Path] = None,
) -> PipelineInput:
    product = ProductInput.from_dict(read_json(product_path))
    competitors = [CompetitorItem.from_dict(r) for r in read_csv_rows(competitors_path)]
    reviews = [ReviewItem.from_dict(r) for r in read_csv_rows(reviews_path)]
    metrics = [MetricsRow.from_dict(r) for r in read_csv_rows(metrics_path)]
    return PipelineInput(product=product, competitors=competitors, reviews=reviews, metrics=metrics)


def slugify(text: str, max_len: int = 32) -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "campaign"


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def render_markdown(output: CampaignOutput) -> str:
    data = output.to_dict()
    product = data["product_summary"]
    lines: List[str] = []

    lines.append(f"# 电商运营 Agent 生成报告：{product.get('name', '')}\n")
    lines.append("## 1. 商品定位")
    lines.append(_json_block(product))

    lines.append("\n## 2. 竞品分析")
    comp = data["competitor_analysis"]
    lines.extend(_dict_section(comp))

    lines.append("\n## 3. 用户洞察")
    insights = data["user_insights"]
    lines.extend(_dict_section(insights))

    lines.append("\n## 4. 标题与详情页文案")
    copy = data["copywriting"]
    if copy.get("titles"):
        lines.append("### 标题备选")
        for i, title in enumerate(copy["titles"], 1):
            lines.append(f"{i}. {title}")
    if copy.get("short_descriptions"):
        lines.append("\n### 短描述")
        for i, desc in enumerate(copy["short_descriptions"], 1):
            lines.append(f"{i}. {desc}")
    if copy.get("detail_page"):
        lines.append("\n### 详情页结构")
        lines.extend(_dict_section(copy["detail_page"]))
    if copy.get("keywords"):
        lines.append("\n### 关键词")
        lines.append("、".join(map(str, copy["keywords"])))

    lines.append("\n## 5. 短视频脚本")
    scripts = data["video_scripts"].get("scripts", [])
    for s in scripts:
        lines.append(f"### {s.get('name', '脚本')}")
        lines.extend(_dict_section(s))

    lines.append("\n## 6. 客服 FAQ")
    faq_items = data["faq"].get("items", [])
    for i, item in enumerate(faq_items, 1):
        lines.append(f"**Q{i}: {item.get('question', '')}**")
        lines.append(f"A: {item.get('answer', '')}")
        if item.get("risk_level"):
            lines.append(f"风险等级：{item.get('risk_level')}")
        lines.append("")

    lines.append("\n## 7. A/B 测试与复盘计划")
    lines.extend(_dict_section(data["growth_plan"]))

    lines.append("\n## 8. 合规检查")
    lines.extend(_dict_section(data["compliance_check"]))

    return "\n".join(lines).strip() + "\n"


def _json_block(obj: Any) -> str:
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def _dict_section(obj: Any, level: int = 0) -> List[str]:
    lines: List[str] = []
    indent = "  " * level
    if isinstance(obj, dict):
        for k, v in obj.items():
            title = str(k).replace("_", " ")
            if isinstance(v, (dict, list)):
                lines.append(f"{indent}- **{title}**:")
                lines.extend(_dict_section(v, level + 1))
            else:
                lines.append(f"{indent}- **{title}**: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.extend(_dict_section(item, level))
            else:
                lines.append(f"{indent}- {item}")
    else:
        lines.append(f"{indent}- {obj}")
    return lines


def save_outputs(output: CampaignOutput, out_dir: str | Path = "outputs") -> Dict[str, str]:
    product_name = output.product_summary.get("name", "campaign")
    folder = Path(out_dir) / f"{now_id()}-{slugify(product_name)}"
    folder.mkdir(parents=True, exist_ok=True)

    json_path = folder / "campaign.json"
    md_path = folder / "campaign.md"

    write_json(json_path, output.to_dict())
    md_path.write_text(render_markdown(output), encoding="utf-8")

    return {"folder": str(folder), "json": str(json_path), "markdown": str(md_path)}
