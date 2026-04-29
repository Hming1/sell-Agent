from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ProductInput:
    name: str
    brand: str = ""
    category: str = ""
    price: str = ""
    target_user: str = ""
    pain_points: List[str] = field(default_factory=list)
    selling_points: List[str] = field(default_factory=list)
    specs: Dict[str, Any] = field(default_factory=dict)
    tone: str = "专业、真实、有转化力，不夸大"
    platform: str = "淘宝/抖音/小红书/独立站"
    keywords: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=lambda: [
        "不编造销量、奖项、认证、功效",
        "不使用绝对化极限词，如最强、全网第一、100%有效",
        "输出内容必须能被运营直接二次编辑"
    ])

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ProductInput":
        return ProductInput(
            name=str(data.get("name", "")).strip(),
            brand=str(data.get("brand", "")).strip(),
            category=str(data.get("category", "")).strip(),
            price=str(data.get("price", "")).strip(),
            target_user=str(data.get("target_user", "")).strip(),
            pain_points=list(data.get("pain_points", []) or []),
            selling_points=list(data.get("selling_points", []) or []),
            specs=dict(data.get("specs", {}) or {}),
            tone=str(data.get("tone", "专业、真实、有转化力，不夸大")),
            platform=str(data.get("platform", "淘宝/抖音/小红书/独立站")),
            keywords=list(data.get("keywords", []) or []),
            constraints=list(data.get("constraints", []) or [
                "不编造销量、奖项、认证、功效",
                "不使用绝对化极限词，如最强、全网第一、100%有效",
                "输出内容必须能被运营直接二次编辑"
            ]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompetitorItem:
    title: str
    price: str = ""
    rating: str = ""
    sales: str = ""
    review_summary: str = ""
    url: str = ""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CompetitorItem":
        return CompetitorItem(
            title=str(data.get("title", "")).strip(),
            price=str(data.get("price", "")).strip(),
            rating=str(data.get("rating", "")).strip(),
            sales=str(data.get("sales", "")).strip(),
            review_summary=str(data.get("review_summary", "")).strip(),
            url=str(data.get("url", "")).strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewItem:
    content: str
    rating: str = ""
    source: str = ""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ReviewItem":
        return ReviewItem(
            content=str(data.get("content", "")).strip(),
            rating=str(data.get("rating", "")).strip(),
            source=str(data.get("source", "")).strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricsRow:
    variant_id: str
    title: str = ""
    exposure: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    spend: float = 0.0

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MetricsRow":
        def to_int(x: Any) -> int:
            try:
                return int(float(str(x).replace(",", "")))
            except Exception:
                return 0

        def to_float(x: Any) -> float:
            try:
                return float(str(x).replace(",", ""))
            except Exception:
                return 0.0

        return MetricsRow(
            variant_id=str(data.get("variant_id", "")).strip(),
            title=str(data.get("title", "")).strip(),
            exposure=to_int(data.get("exposure", 0)),
            clicks=to_int(data.get("clicks", 0)),
            conversions=to_int(data.get("conversions", 0)),
            revenue=to_float(data.get("revenue", 0)),
            spend=to_float(data.get("spend", 0)),
        )

    def ctr(self) -> float:
        return self.clicks / self.exposure if self.exposure else 0.0

    def cvr(self) -> float:
        return self.conversions / self.clicks if self.clicks else 0.0

    def roas(self) -> float:
        return self.revenue / self.spend if self.spend else 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["ctr"] = round(self.ctr(), 4)
        d["cvr"] = round(self.cvr(), 4)
        d["roas"] = round(self.roas(), 4)
        return d


@dataclass
class PipelineInput:
    product: ProductInput
    competitors: List[CompetitorItem] = field(default_factory=list)
    reviews: List[ReviewItem] = field(default_factory=list)
    metrics: List[MetricsRow] = field(default_factory=list)


@dataclass
class CampaignOutput:
    product_summary: Dict[str, Any]
    competitor_analysis: Dict[str, Any]
    user_insights: Dict[str, Any]
    copywriting: Dict[str, Any]
    video_scripts: Dict[str, Any]
    faq: Dict[str, Any]
    growth_plan: Dict[str, Any]
    compliance_check: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
