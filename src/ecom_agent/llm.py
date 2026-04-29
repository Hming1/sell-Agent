from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Dict, Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


class LLMClient:
    """
    Thin wrapper around the OpenAI Responses API.

    - If OPENAI_API_KEY exists, the agents call the model.
    - If not, every agent returns deterministic fallback content, so the demo still runs.
    """

    def __init__(self, model: Optional[str] = None, enabled: Optional[bool] = None) -> None:
        if load_dotenv:
            load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.enabled = bool(self.api_key) if enabled is None else enabled
        self.client = None

        if self.enabled:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None
                self.enabled = False

    def generate_json(
        self,
        system: str,
        user: str,
        fallback: Callable[[], Dict[str, Any]],
        temperature: float = 0.4,
    ) -> Dict[str, Any]:
        if not self.enabled or self.client is None:
            result = fallback()
            result["_source"] = "fallback_no_api_key"
            return result

        strict_user = (
            user
            + "\n\n请只输出一个合法 JSON 对象，不要输出 Markdown 代码块，不要输出解释。"
            + "所有字段必须使用中文，数组字段请至少给出 3 条。"
        )
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system,
                input=strict_user,
                temperature=temperature,
            )
        except Exception:
            # Some models do not accept temperature. Retry once without it.
            try:
                response = self.client.responses.create(
                    model=self.model,
                    instructions=system,
                    input=strict_user,
                )
            except Exception as e:
                result = fallback()
                result["_source"] = "fallback_llm_error"
                result["_llm_error"] = str(e)[:500]
                return result

        text = getattr(response, "output_text", "") or ""
        try:
            parsed = parse_json_text(text)
            if isinstance(parsed, dict):
                parsed["_source"] = "llm"
                return parsed
        except Exception as e:
            result = fallback()
            result["_source"] = "fallback_parse_error"
            result["_parse_error"] = str(e)[:500]
            result["_raw_text"] = text[:1000]
            return result

        result = fallback()
        result["_source"] = "fallback_empty_llm_output"
        return result


def parse_json_text(text: str) -> Any:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"```$", "", s).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    obj_start = s.find("{")
    obj_end = s.rfind("}")
    if obj_start >= 0 and obj_end > obj_start:
        return json.loads(s[obj_start : obj_end + 1])

    arr_start = s.find("[")
    arr_end = s.rfind("]")
    if arr_start >= 0 and arr_end > arr_start:
        return json.loads(s[arr_start : arr_end + 1])

    raise ValueError("No JSON object or array found in model output")
