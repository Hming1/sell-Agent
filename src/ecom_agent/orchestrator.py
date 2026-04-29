from __future__ import annotations

from typing import Any, Dict

from .agents import (
    ComplianceAgent,
    CompetitorAnalysisAgent,
    CopywritingAgent,
    FAQAgent,
    GrowthAgent,
    ProductSummaryAgent,
    UserInsightAgent,
    VideoScriptAgent,
)
from .io_utils import load_pipeline_input, save_outputs
from .llm import LLMClient
from .models import CampaignOutput, PipelineInput


class EcommerceAgentOrchestrator:
    """Coordinates all specialist agents into one e-commerce launch pipeline."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.product_agent = ProductSummaryAgent(self.llm)
        self.competitor_agent = CompetitorAnalysisAgent(self.llm)
        self.insight_agent = UserInsightAgent(self.llm)
        self.copy_agent = CopywritingAgent(self.llm)
        self.video_agent = VideoScriptAgent(self.llm)
        self.faq_agent = FAQAgent(self.llm)
        self.growth_agent = GrowthAgent(self.llm)
        self.compliance_agent = ComplianceAgent(self.llm)

    def run(self, data: PipelineInput) -> CampaignOutput:
        product = data.product
        product_summary = self.product_agent.run(product)
        competitor_analysis = self.competitor_agent.run(product, data.competitors)
        user_insights = self.insight_agent.run(product, data.reviews, data.competitors)
        copywriting = self.copy_agent.run(product, competitor_analysis, user_insights)
        video_scripts = self.video_agent.run(product, user_insights, copywriting)
        faq = self.faq_agent.run(product, user_insights, competitor_analysis)
        growth_plan = self.growth_agent.run(product, data.metrics, copywriting, video_scripts)

        generated_bundle: Dict[str, Any] = {
            "competitor_analysis": competitor_analysis,
            "user_insights": user_insights,
            "copywriting": copywriting,
            "video_scripts": video_scripts,
            "faq": faq,
            "growth_plan": growth_plan,
        }
        compliance_check = self.compliance_agent.run(generated_bundle, product)

        return CampaignOutput(
            product_summary=product_summary,
            competitor_analysis=competitor_analysis,
            user_insights=user_insights,
            copywriting=copywriting,
            video_scripts=video_scripts,
            faq=faq,
            growth_plan=growth_plan,
            compliance_check=compliance_check,
        )


def run_from_paths(
    product_path: str,
    competitors_path: str | None = None,
    reviews_path: str | None = None,
    metrics_path: str | None = None,
    out_dir: str = "outputs",
    llm: LLMClient | None = None,
) -> Dict[str, str]:
    data = load_pipeline_input(product_path, competitors_path, reviews_path, metrics_path)
    output = EcommerceAgentOrchestrator(llm=llm).run(data)
    return save_outputs(output, out_dir=out_dir)
