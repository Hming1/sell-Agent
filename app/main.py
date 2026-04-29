from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, HTTPException

from ecom_agent.llm import LLMClient
from ecom_agent.models import CompetitorItem, MetricsRow, PipelineInput, ProductInput, ReviewItem
from ecom_agent.orchestrator import EcommerceAgentOrchestrator

app = FastAPI(title="E-commerce Operations Agent", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/generate")
def generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "product" not in payload:
        raise HTTPException(status_code=400, detail="Missing required field: product")

    product = ProductInput.from_dict(payload.get("product", {}))
    competitors = [CompetitorItem.from_dict(x) for x in payload.get("competitors", [])]
    reviews = [ReviewItem.from_dict(x) for x in payload.get("reviews", [])]
    metrics = [MetricsRow.from_dict(x) for x in payload.get("metrics", [])]
    use_llm = bool(payload.get("use_llm", True))
    model = payload.get("model")

    llm = LLMClient(model=model, enabled=use_llm)
    output = EcommerceAgentOrchestrator(llm=llm).run(
        PipelineInput(product=product, competitors=competitors, reviews=reviews, metrics=metrics)
    )
    return output.to_dict()
