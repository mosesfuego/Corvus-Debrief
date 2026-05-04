"""Classify manufacturing data sources from headers and samples."""

from intake.mapping_registry import SOURCE_TYPE_KEYWORDS, normalize_name


def classify_headers(headers: list[str]) -> dict:
    """Classify a CSV/API payload by header names."""
    normalized = [normalize_name(h) for h in headers]
    scores = {}

    for source_type, keywords in SOURCE_TYPE_KEYWORDS.items():
        score = 0
        for header in normalized:
            for keyword in keywords:
                key = normalize_name(keyword)
                if header == key or key in header:
                    score += 1
        scores[source_type] = score

    best_type = max(scores, key=scores.get, default="unknown")
    best_score = scores.get(best_type, 0)
    if best_score == 0:
        best_type = "unknown"

    total = sum(scores.values()) or 1
    confidence = round(best_score / total, 2) if best_type != "unknown" else 0.0

    return {
        "source_type": best_type,
        "confidence": confidence,
        "scores": scores,
    }


def classify_rows(headers: list[str], rows: list[dict] | None = None) -> dict:
    """Classify rows; currently header-driven with room for sample heuristics."""
    return classify_headers(headers)

