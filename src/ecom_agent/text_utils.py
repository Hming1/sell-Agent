from __future__ import annotations

import json
import re
from collections import Counter
from statistics import median
from typing import Any, Dict, Iterable, List, Sequence


STOPWORDS = {
    "的", "了", "和", "是", "就", "都", "而", "及", "与", "着", "或", "一个", "没有", "我们", "你们",
    "this", "that", "with", "from", "your", "for", "the", "and", "or", "is", "are", "to", "of", "in"
}


def compact_json(obj: Any, max_chars: int = 6000) -> str:
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    return s[:max_chars]


def safe_join(items: Iterable[Any], sep: str = "、") -> str:
    return sep.join(str(x) for x in items if str(x).strip())


def extract_number(text: str) -> float | None:
    if not text:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(text).replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def price_stats(prices: Sequence[str]) -> Dict[str, Any]:
    nums = [extract_number(p) for p in prices]
    nums = [n for n in nums if n is not None]
    if not nums:
        return {"min": None, "median": None, "max": None, "count": 0}
    return {
        "min": round(min(nums), 2),
        "median": round(median(nums), 2),
        "max": round(max(nums), 2),
        "count": len(nums),
    }


def simple_keywords(texts: Iterable[str], top_k: int = 12) -> List[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        if not text:
            continue
        text = str(text).lower()
        # English words and numbers.
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", text):
            if token not in STOPWORDS:
                counter[token] += 1
        # Chinese chunks split by punctuation and spaces.
        chunks = re.split(r"[\s,，。！？!?:：；;、/|\\()（）\[\]【】{}<>《》\-]+", text)
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 2:
                continue
            if re.fullmatch(r"[\u4e00-\u9fff]{2,12}", chunk) and chunk not in STOPWORDS:
                counter[chunk] += 1
            # Add 2-4 char ngrams for longer Chinese phrases.
            if re.fullmatch(r"[\u4e00-\u9fff]{5,}", chunk):
                for n in (2, 3, 4):
                    for i in range(0, len(chunk) - n + 1):
                        gram = chunk[i : i + n]
                        if gram not in STOPWORDS:
                            counter[gram] += 1
    return [w for w, _ in counter.most_common(top_k)]


def top_metric_variants(rows: Sequence[Any], top_k: int = 3) -> List[Dict[str, Any]]:
    if not rows:
        return []
    scored = []
    for r in rows:
        score = r.cvr() * 0.45 + r.ctr() * 0.35 + min(r.roas(), 10) / 10 * 0.20
        d = r.to_dict()
        d["score"] = round(score, 4)
        scored.append(d)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]
