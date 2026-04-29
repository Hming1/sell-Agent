from __future__ import annotations

import re
from typing import Any, Dict, List

from .llm import LLMClient
from .models import CompetitorItem, MetricsRow, PipelineInput, ProductInput, ReviewItem
from .text_utils import compact_json, price_stats, safe_join, simple_keywords, top_metric_variants


class BaseAgent:
    name = "base_agent"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()


class ProductSummaryAgent(BaseAgent):
    name = "product_summary_agent"

    def run(self, product: ProductInput) -> Dict[str, Any]:
        return {
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "price": product.price,
            "platform": product.platform,
            "target_user": product.target_user,
            "core_pain_points": product.pain_points,
            "core_selling_points": product.selling_points,
            "specs": product.specs,
            "tone": product.tone,
            "keywords": product.keywords,
            "constraints": product.constraints,
        }


class CompetitorAnalysisAgent(BaseAgent):
    name = "competitor_analysis_agent"

    def run(self, product: ProductInput, competitors: List[CompetitorItem]) -> Dict[str, Any]:
        comp_dicts = [c.to_dict() for c in competitors]
        prices = price_stats([c.price for c in competitors])
        keywords = simple_keywords([c.title + " " + c.review_summary for c in competitors], top_k=16)

        def fallback() -> Dict[str, Any]:
            if not competitors:
                return {
                    "price_band": prices,
                    "market_positioning": "暂未导入竞品数据，建议先补充 5-20 个同类商品标题、价格、评价摘要。",
                    "competitor_patterns": ["竞品数据不足，先用商品卖点和目标人群生成初版内容。"],
                    "opportunities": [
                        "把卖点表达从参数堆砌改为场景收益",
                        "围绕用户痛点生成对比型标题",
                        "在详情页增加使用场景、规格说明和售后问题"
                    ],
                    "risk_points": ["缺少竞品价格带，定价建议置信度较低"],
                    "differentiation_strategy": ["突出真实使用场景", "突出具体参数和可验证权益", "避免夸大承诺"],
                    "keyword_candidates": product.keywords,
                }
            return {
                "price_band": prices,
                "market_positioning": f"参考 {len(competitors)} 个竞品，当前商品应避免只拼低价，建议用场景化利益点切入。",
                "competitor_patterns": [
                    f"竞品标题高频词：{safe_join(keywords[:8])}",
                    "多数竞品会强调核心参数、价格和立即可感知的使用收益。",
                    "评价摘要中反复出现的问题可转化为 FAQ 和详情页信任模块。",
                ],
                "opportunities": [
                    "从用户痛点出发，标题中同时放入人群、场景和核心卖点。",
                    "详情页第一屏先回答为什么需要它，再展开参数。",
                    "把负面评价担忧转化为购买前说明，降低售前咨询成本。",
                ],
                "risk_points": [
                    "不要直接复制竞品标题结构和独特表达。",
                    "不要虚构销量、平台背书、认证和用户评价。",
                    "高客单价商品需要补充质保、售后或退换说明。",
                ],
                "differentiation_strategy": [
                    "同类低价品多时，强调稳定性、细节和售后；同类高价品多时，强调性价比和关键功能。",
                    "用具体规格支撑卖点，用使用场景承接转化。",
                    "短视频重点做 3 秒钩子：痛点画面 + 结果反差。",
                ],
                "keyword_candidates": keywords,
            }

        system = "你是资深电商竞品分析师，擅长从竞品标题、价格、评价中提炼定位机会。"
        user = f"""
请基于以下商品和竞品数据做竞品分析。

商品：
{compact_json(product.to_dict())}

竞品数据：
{compact_json(comp_dicts, max_chars=9000)}

必须输出 JSON，结构如下：
{{
  "price_band": {{"min": 数字或null, "median": 数字或null, "max": 数字或null, "count": 数字}},
  "market_positioning": "一句话市场定位建议",
  "competitor_patterns": ["竞品共性 1", "竞品共性 2", "竞品共性 3"],
  "opportunities": ["机会点 1", "机会点 2", "机会点 3"],
  "risk_points": ["风险点 1", "风险点 2", "风险点 3"],
  "differentiation_strategy": ["差异化策略 1", "差异化策略 2", "差异化策略 3"],
  "keyword_candidates": ["关键词"]
}}
"""
        result = self.llm.generate_json(system, user, fallback)
        # Keep deterministic price stats when LLM output omits it.
        result.setdefault("price_band", prices)
        result.setdefault("keyword_candidates", keywords)
        return result


class UserInsightAgent(BaseAgent):
    name = "user_insight_agent"

    def run(self, product: ProductInput, reviews: List[ReviewItem], competitors: List[CompetitorItem]) -> Dict[str, Any]:
        review_dicts = [r.to_dict() for r in reviews]
        review_keywords = simple_keywords([r.content for r in reviews], top_k=16)
        comp_review_keywords = simple_keywords([c.review_summary for c in competitors], top_k=10)

        def fallback() -> Dict[str, Any]:
            pain_points = product.pain_points or ["选择成本高", "担心质量不稳定", "担心买回去不适合自己的使用场景"]
            triggers = product.selling_points or ["省时", "好用", "稳定", "适合日常场景"]
            return {
                "target_persona": product.target_user or "对同类商品有明确需求、希望快速判断是否值得购买的用户",
                "top_pain_points": pain_points[:5],
                "buying_triggers": triggers[:5],
                "objections": [
                    "价格是否值得",
                    "实际效果是否和描述一致",
                    "售后、退换、使用门槛是否清楚",
                ],
                "voice_of_customer": review_keywords[:8] or comp_review_keywords[:8] or product.keywords,
                "content_angles": [
                    "痛点前置：先说用户正在遇到什么麻烦",
                    "场景证明：展示具体使用场景和前后变化",
                    "信任补充：用规格、材质、服务、注意事项降低顾虑",
                ],
            }

        system = "你是电商用户洞察分析师，擅长从用户评价和竞品反馈中提炼购买动机、顾虑和内容角度。"
        user = f"""
请分析商品的目标用户、痛点、购买触发点和阻碍转化的顾虑。

商品：
{compact_json(product.to_dict())}

用户评价：
{compact_json(review_dicts, max_chars=9000)}

竞品评价摘要关键词：{safe_join(comp_review_keywords)}

输出 JSON：
{{
  "target_persona": "目标用户画像",
  "top_pain_points": ["痛点"],
  "buying_triggers": ["购买触发点"],
  "objections": ["购买顾虑"],
  "voice_of_customer": ["用户原声关键词或短语"],
  "content_angles": ["内容切入角度"]
}}
"""
        return self.llm.generate_json(system, user, fallback)


class CopywritingAgent(BaseAgent):
    name = "copywriting_agent"

    def run(self, product: ProductInput, competitor_analysis: Dict[str, Any], user_insights: Dict[str, Any]) -> Dict[str, Any]:
        keyword_candidates = list(dict.fromkeys(
            list(product.keywords)
            + list(competitor_analysis.get("keyword_candidates", []) or [])
            + list(user_insights.get("voice_of_customer", []) or [])
        ))[:20]

        def fallback() -> Dict[str, Any]:
            name = product.name
            sp = product.selling_points or ["实用", "省心", "适合日常使用"]
            pain = product.pain_points or ["选择麻烦", "使用不顺手", "担心踩坑"]
            target = product.target_user or "日常用户"
            titles = [
                f"{name}｜解决{pain[0]}，{sp[0]}更省心",
                f"适合{target}的{name}，把{sp[0]}做到日常可用",
                f"别再为{pain[0]}纠结：这款{name}主打{safe_join(sp[:2])}",
                f"{name}上新：{safe_join(sp[:3])}，适合{target}",
                f"想要{sp[0]}？先看这款{name}的真实使用场景",
                f"{name}详情解析：规格、场景、常见问题一次看清",
                f"从{pain[0]}到省心使用，{name}帮你少走弯路",
                f"{target}可入：{name}，重点看这 3 个细节",
                f"{name}不是越复杂越好，关键是{sp[0]}和稳定体验",
                f"新手也能快速判断：{name}适不适合你",
            ]
            return {
                "titles": titles,
                "short_descriptions": [
                    f"围绕{safe_join(sp[:3])}设计，适合{target}在日常场景中使用。",
                    f"针对{safe_join(pain[:2])}等问题，提供更清晰、可执行的选择方案。",
                    f"不堆概念，重点讲清楚规格、场景和购买前需要知道的注意事项。",
                ],
                "hero_slogan": f"把{pain[0]}变成省心体验",
                "detail_page": {
                    "first_screen": f"一句话说明：{name}适合{target}，核心价值是{safe_join(sp[:3])}。",
                    "pain_scene": [f"用户常见问题：{x}" for x in pain[:4]],
                    "selling_point_sections": [
                        {"title": f"卖点 {i+1}：{point}", "copy": f"用具体场景解释 {point}，避免空泛承诺。"}
                        for i, point in enumerate(sp[:5])
                    ],
                    "spec_module": [f"{k}: {v}" for k, v in product.specs.items()] or ["补充核心规格参数，帮助用户快速对比。"],
                    "trust_module": ["明确适用场景", "明确不适用场景", "说明售后或使用注意事项"],
                    "cta": "现在下单/咨询客服，先确认你的使用场景是否匹配。",
                },
                "keywords": keyword_candidates,
            }

        system = "你是电商转化文案专家，擅长生成合规、具体、可直接投放的标题、详情页和卖点文案。"
        user = f"""
请为以下商品生成上新所需文案，平台：{product.platform}。

商品：
{compact_json(product.to_dict())}

竞品分析：
{compact_json(competitor_analysis)}

用户洞察：
{compact_json(user_insights)}

要求：
1. 不夸大，不编造销量、认证、用户反馈。
2. 标题要有差异化，避免重复同一种句式。
3. 文案能直接给运营二次编辑。

输出 JSON：
{{
  "titles": ["至少 10 个标题"],
  "short_descriptions": ["3-5 条短描述"],
  "hero_slogan": "详情页首屏 slogan",
  "detail_page": {{
    "first_screen": "首屏核心文案",
    "pain_scene": ["痛点场景"],
    "selling_point_sections": [{{"title": "模块标题", "copy": "模块正文"}}],
    "spec_module": ["规格说明"],
    "trust_module": ["信任模块"],
    "cta": "行动引导"
  }},
  "keywords": ["关键词"]
}}
"""
        result = self.llm.generate_json(system, user, fallback, temperature=0.6)
        result.setdefault("keywords", keyword_candidates)
        return result


class VideoScriptAgent(BaseAgent):
    name = "video_script_agent"

    def run(self, product: ProductInput, user_insights: Dict[str, Any], copywriting: Dict[str, Any]) -> Dict[str, Any]:
        def fallback() -> Dict[str, Any]:
            name = product.name
            pain = (user_insights.get("top_pain_points") or product.pain_points or ["这个问题"])[0]
            sp = product.selling_points or ["省心", "实用", "适合日常"]
            return {
                "scripts": [
                    {
                        "name": "痛点反差型 30 秒",
                        "hook": f"你是不是也被{pain}困扰？",
                        "scenes": [
                            "0-3s：展示用户痛点画面，字幕点出问题",
                            f"3-8s：拿出 {name}，说明它解决的具体场景",
                            f"8-20s：展示 {safe_join(sp[:3])}，每个卖点配一个使用镜头",
                            "20-27s：展示规格/细节/注意事项，建立信任",
                            "27-30s：引导评论或咨询适用场景",
                        ],
                        "caption": f"不是所有人都需要复杂方案，{name}把关键体验做清楚。",
                        "cta": "评论你的使用场景，我帮你判断是否适合。",
                    },
                    {
                        "name": "开箱测评型 45 秒",
                        "hook": f"这款{name}，我会重点看这 3 个细节。",
                        "scenes": [
                            "0-5s：快速开箱，展示全套配件/外观",
                            "5-15s：讲第一个核心卖点，并展示细节",
                            "15-25s：讲第二个核心卖点，并展示使用场景",
                            "25-35s：讲可能不适合的人群，增强真实感",
                            "35-45s：总结适合谁、购买前看什么",
                        ],
                        "caption": f"{name}购买前先看细节，不要只看标题。",
                        "cta": "想看对比或实测，留言关键词。",
                    },
                    {
                        "name": "竞品对比型 30 秒",
                        "hook": "同类产品怎么选？不要只看价格。",
                        "scenes": [
                            "0-4s：展示常见选择误区",
                            f"4-12s：说明 {name} 的定位和适用人群",
                            "12-22s：用三个维度对比：场景、规格、售后/注意事项",
                            "22-30s：给出选择建议，不贬低竞品",
                        ],
                        "caption": "对比不是拉踩，而是帮你判断是否匹配需求。",
                        "cta": "收藏这条，购买前按这 3 点检查。",
                    },
                ]
            }

        system = "你是短视频电商编导，擅长生成可拍摄、合规、有转化力的口播和分镜。"
        user = f"""
请为商品生成 3 条短视频脚本，分别适配痛点反差、开箱测评、竞品对比。

商品：{compact_json(product.to_dict())}
用户洞察：{compact_json(user_insights)}
文案素材：{compact_json(copywriting)}

输出 JSON：
{{
  "scripts": [
    {{"name": "脚本名称", "hook": "3秒钩子", "scenes": ["分镜"], "caption": "发布文案", "cta": "行动引导"}}
  ]
}}
"""
        return self.llm.generate_json(system, user, fallback, temperature=0.7)


class FAQAgent(BaseAgent):
    name = "faq_agent"

    def run(self, product: ProductInput, user_insights: Dict[str, Any], competitor_analysis: Dict[str, Any]) -> Dict[str, Any]:
        def fallback() -> Dict[str, Any]:
            sp = product.selling_points or ["核心功能", "使用体验", "适用场景"]
            objections = user_insights.get("objections") or ["是否适合我", "价格是否值得", "售后如何"]
            questions = [
                ("这款产品适合什么人？", f"适合{product.target_user or '有相关使用需求的用户'}，建议结合自己的使用场景判断。"),
                ("它主要解决什么问题？", f"主要围绕{safe_join(product.pain_points[:3]) or '日常使用痛点'}，提供更省心的选择。"),
                ("和同类产品相比有什么不同？", f"重点在{safe_join(sp[:3])}，不是单纯堆参数或拼低价。"),
                ("购买前需要注意什么？", "建议确认规格、适用场景、售后规则和自己的预算。"),
                ("是否有售后保障？", "请以店铺实际售后政策为准，可在下单前咨询客服确认。"),
                ("新手能不能使用？", "如果使用方式较简单，可以按说明操作；若有特殊场景，建议先咨询。"),
                ("发货包含哪些内容？", "以商品详情页和订单页面展示为准，避免因套餐不同产生误解。"),
                ("价格为什么和其他商品不一样？", "价格会受到规格、材质、服务、活动等因素影响，建议按需求对比。"),
                ("如何判断是否适合自己？", "可以告诉客服你的使用场景、预算和期望效果，再判断是否匹配。"),
                ("评价里提到的问题怎么处理？", "不同用户场景不同，建议重点看与你场景相似的反馈。"),
                ("能不能用于特殊场景？", "特殊场景建议先确认规格和限制，避免买错。"),
                ("有没有使用建议？", "首次使用建议按说明进行，并保留包装和订单信息方便售后。"),
            ]
            for obj in objections[:3]:
                questions.append((f"关于“{obj}”应该怎么判断？", f"建议结合实际使用场景确认，必要时咨询客服，不做夸大承诺。"))
            return {
                "items": [
                    {"question": q, "answer": a, "risk_level": "低" if i < 10 else "中"}
                    for i, (q, a) in enumerate(questions[:12])
                ]
            }

        system = "你是电商客服 SOP 专家，擅长生成低风险、真实、可直接使用的 FAQ。"
        user = f"""
请为商品生成客服 FAQ，用于商品上新后的售前咨询。

商品：{compact_json(product.to_dict())}
用户洞察：{compact_json(user_insights)}
竞品分析：{compact_json(competitor_analysis)}

要求：
1. 至少 12 个问题。
2. 对涉及售后、效果、发货、适用限制的问题，回答要保守，提示以实际政策为准。
3. 不要虚构认证、活动、库存、物流时效。

输出 JSON：
{{
  "items": [{{"question": "问题", "answer": "回答", "risk_level": "低/中/高"}}]
}}
"""
        return self.llm.generate_json(system, user, fallback, temperature=0.3)


class GrowthAgent(BaseAgent):
    name = "growth_agent"

    def run(
        self,
        product: ProductInput,
        metrics: List[MetricsRow],
        copywriting: Dict[str, Any],
        video_scripts: Dict[str, Any],
    ) -> Dict[str, Any]:
        top_rows = top_metric_variants(metrics)
        metric_dicts = [m.to_dict() for m in metrics]

        def fallback() -> Dict[str, Any]:
            title_variants = copywriting.get("titles", [])[:4]
            return {
                "current_winners": top_rows,
                "ab_test_plan": [
                    {
                        "test_name": "标题利益点测试",
                        "variants": title_variants or ["痛点型标题", "场景型标题", "参数型标题", "人群型标题"],
                        "success_metric": "CTR 点击率",
                        "decision_rule": "曝光量达到 1000 后，优先保留 CTR 高于均值 15% 且转化不下降的版本。",
                    },
                    {
                        "test_name": "详情页首屏测试",
                        "variants": ["痛点前置", "卖点前置", "场景前置"],
                        "success_metric": "CVR 转化率",
                        "decision_rule": "点击量达到 300 后，比较下单转化和客服咨询率。",
                    },
                    {
                        "test_name": "短视频钩子测试",
                        "variants": [s.get("hook", "") for s in video_scripts.get("scripts", [])][:3] or ["痛点钩子", "测评钩子", "对比钩子"],
                        "success_metric": "3秒留存/完播率/商品点击率",
                        "decision_rule": "优先放大留存高且商品点击率高的脚本。",
                    },
                ],
                "metrics_to_track": ["曝光", "点击", "CTR", "收藏加购", "咨询率", "CVR", "客单价", "ROAS", "退款原因"],
                "optimization_rules": [
                    "CTR 低：优先调整标题前 12 个字、主图卖点和人群场景。",
                    "CTR 高但 CVR 低：检查详情页承接、价格预期、FAQ 和售后说明。",
                    "咨询多但下单少：把高频咨询问题前置到详情页和短视频。",
                    "退款或差评集中：暂停放大投放，先修正文案预期和商品说明。",
                ],
                "next_iteration_prompts": [
                    "基于最高 CTR 标题，总结共性并再生成 10 个变体。",
                    "根据客服高频问题，重写详情页第一屏和 FAQ。",
                    "根据低转化原因，生成 3 个更保守但更精准的短视频脚本。",
                ],
            }

        system = "你是电商增长运营专家，擅长根据内容素材和转化数据制定 A/B 测试与迭代计划。"
        user = f"""
请为商品制定上新后的 A/B 测试和内容复盘计划。

商品：{compact_json(product.to_dict())}
历史指标：{compact_json(metric_dicts, max_chars=9000)}
标题与详情页：{compact_json(copywriting)}
短视频脚本：{compact_json(video_scripts)}

输出 JSON：
{{
  "current_winners": [{{"variant_id": "", "title": "", "ctr": 0.0, "cvr": 0.0, "roas": 0.0, "score": 0.0}}],
  "ab_test_plan": [{{"test_name": "", "variants": [""], "success_metric": "", "decision_rule": ""}}],
  "metrics_to_track": ["指标"],
  "optimization_rules": ["优化规则"],
  "next_iteration_prompts": ["下一轮迭代 Prompt"]
}}
"""
        result = self.llm.generate_json(system, user, fallback, temperature=0.4)
        result.setdefault("current_winners", top_rows)
        return result


class ComplianceAgent(BaseAgent):
    name = "compliance_agent"

    FORBIDDEN_PATTERNS = [
        r"全网第一", r"第一名", r"最强", r"最好", r"绝对", r"100%", r"永久", r"包治", r"无效退款",
        r"国家级", r"唯一", r"顶级", r"销量第一", r"零风险", r"立刻见效",
    ]

    def run(self, generated: Dict[str, Any], product: ProductInput) -> Dict[str, Any]:
        text = compact_json(generated, max_chars=50000)
        hits: List[str] = []
        for pat in self.FORBIDDEN_PATTERNS:
            if re.search(pat, text, flags=re.IGNORECASE):
                hits.append(pat)
        issues: List[str] = []
        if hits:
            issues.append(f"发现可能的夸大或极限表达：{safe_join(hits)}")
        if "认证" in text and "认证" not in compact_json(product.to_dict()):
            issues.append("文案中出现认证相关表达，请确认商品资料是否真实提供。")
        if "销量" in text and "销量" not in compact_json(product.to_dict()):
            issues.append("文案中出现销量相关表达，请确认不是模型编造。")
        return {
            "pass": len(issues) == 0,
            "issues": issues,
            "safe_rewrite_rules": [
                "把绝对化表达改成场景化表达，例如“更适合日常使用”。",
                "把无法验证的结果承诺改成“建议根据实际使用场景判断”。",
                "把认证、销量、奖项等信息仅保留在商品资料真实提供时。",
            ],
            "manual_review_required": bool(issues),
        }
