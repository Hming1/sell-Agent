from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_utils import load_pipeline_input, save_outputs
from .llm import LLMClient
from .orchestrator import EcommerceAgentOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="E-commerce operations multi-agent pipeline")
    parser.add_argument("--product", required=True, help="Path to product JSON")
    parser.add_argument("--competitors", default=None, help="Path to competitors CSV")
    parser.add_argument("--reviews", default=None, help="Path to reviews CSV")
    parser.add_argument("--metrics", default=None, help="Path to metrics CSV")
    parser.add_argument("--out", default="outputs", help="Output directory")
    parser.add_argument("--model", default=None, help="OpenAI model name. Overrides OPENAI_MODEL.")
    parser.add_argument("--no-llm", action="store_true", help="Run deterministic fallback without calling OpenAI API")
    parser.add_argument("--print-json", action="store_true", help="Print campaign JSON to stdout")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    llm = LLMClient(model=args.model, enabled=not args.no_llm)
    pipeline_input = load_pipeline_input(args.product, args.competitors, args.reviews, args.metrics)
    output = EcommerceAgentOrchestrator(llm=llm).run(pipeline_input)
    paths = save_outputs(output, out_dir=args.out)

    if args.print_json:
        print(json.dumps(output.to_dict(), ensure_ascii=False, indent=2))
    print("\n生成完成：")
    for k, v in paths.items():
        print(f"- {k}: {Path(v).resolve()}")


if __name__ == "__main__":
    main()
