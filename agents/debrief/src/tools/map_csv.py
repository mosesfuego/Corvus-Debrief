"""
Corvus CSV Column Mapper.
Reads any CSV, uses LLM to propose column mapping to Corvus schema,
auto-accepts high confidence fields, prompts on uncertain ones,
saves confirmed mapping + fingerprint to onboarding.yaml.

Usage (from repository root):
    python agents/debrief/src/tools/map_csv.py shared/data/input.csv
    python agents/debrief/src/tools/map_csv.py shared/data/input.csv \\
        --onboarding agents/debrief/config/onboarding.yaml
    python agents/debrief/src/tools/map_csv.py shared/data/input.csv --force
"""

import csv
import sys
import json
import hashlib
import argparse
import os
import traceback

_THIS_FILE = os.path.abspath(__file__)
_SRC_DIR = os.path.dirname(os.path.dirname(_THIS_FILE))
_AGENT_ROOT = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _SRC_DIR)
for _p in (_SHARED_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.append(_p)

import yaml
from openai import OpenAI
from utils.config import load_config, load_onboarding


CORVUS_SCHEMA = {
    "build_id":            "Unique identifier for the work order or job",
    "station_id":          "Machine, line, or workstation where the job runs",
    "operator_id":         "Technician or operator assigned to the job",
    "start_time":          "When the job started (ISO datetime or similar)",
    "planned_end":         "When the job is scheduled to finish",
    "needed_by_date":      "Customer or production deadline for this job",
    "target_quantity":     "How many units are planned for this job",
    "completed_quantity":  "How many units have been completed so far",
    "labor_hours":         "Hours of labor logged against this job",
    "status":              "Current state of the job (e.g. In Progress, Blocked, Completed)",
    "notes":               "Any comments, flags, or free text about this job",
}

REQUIRED_FIELDS = ["build_id", "status"]
CONFIDENCE_THRESHOLD = 0.85


def get_csv_fingerprint(file_path: str) -> str:
    """
    Hash sorted normalized headers + first 3 data rows.
    Detects schema changes and column reorders.
    """
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = []
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 3:
                break

    if not rows:
        raise ValueError("CSV file is empty")

    headers = [h.strip().lower() for h in rows[0]]
    sorted_headers = sorted(headers)
    data_sample = [",".join(r) for r in rows[1:4]]

    fingerprint_input = "|".join(sorted_headers) + "||" + "|".join(data_sample)
    return hashlib.md5(fingerprint_input.encode()).hexdigest()[:12]


def verify_mapping_still_valid(
    column_map: dict,
    current_headers: list[str]
) -> tuple[bool, list[str]]:
    """
    Before skipping LLM call, verify mapped columns
    still exist in the current CSV.
    """
    normalized = [h.strip().lower() for h in current_headers]
    missing = []
    for corvus_field, csv_col in column_map.items():
        if csv_col and csv_col.strip().lower() not in normalized:
            missing.append(f"  '{corvus_field}' → '{csv_col}' (no longer in CSV)")
    return len(missing) == 0, missing


def read_csv_sample(file_path: str) -> tuple[list[str], list[dict]]:
    """Read headers and first 3 rows for LLM context."""
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = []
        for i, row in enumerate(reader):
            rows.append(dict(row))
            if i >= 2:
                break
    return headers, rows


def propose_mapping_with_llm(
    headers: list[str],
    sample_rows: list[dict],
    config: dict
) -> dict:
    """
    Ask LLM to propose column mapping from customer CSV to Corvus schema.
    Returns mapping with confidence scores.
    """
    agent_config = config.get("agents", {})
    client = OpenAI(
        api_key=agent_config["api_key"],
        base_url=agent_config.get("base_url")
    )
    model = agent_config.get("model", "moonshotai/kimi-k2.5")

    schema_description = "\n".join(
        f"{field}: {desc}" for field, desc in CORVUS_SCHEMA.items()
    )
    sample_text = json.dumps(sample_rows, indent=2)

    prompt = f"""
You are a data mapping assistant.
You MUST output valid JSON only.
Do NOT output explanations.
Do NOT output reasoning.
Do NOT output markdown.
Do NOT think step by step.

CORVUS SCHEMA:
{schema_description}

CSV HEADERS:
{headers}

SAMPLE ROWS:
{sample_text}

Return JSON in this format:
{{
  "mapping": {{
    "build_id": {{"csv_column": "...", "confidence": 0.0}},
    "station_id": {{"csv_column": "...", "confidence": 0.0}},
    "operator_id": {{"csv_column": "...", "confidence": 0.0}},
    "start_time": {{"csv_column": "...", "confidence": 0.0}},
    "planned_end": {{"csv_column": "...", "confidence": 0.0}},
    "needed_by_date": {{"csv_column": "...", "confidence": 0.0}},
    "target_quantity": {{"csv_column": "...", "confidence": 0.0}},
    "completed_quantity": {{"csv_column": "...", "confidence": 0.0}},
    "labor_hours": {{"csv_column": "...", "confidence": 0.0}},
    "status": {{"csv_column": "...", "confidence": 0.0}},
    "notes": {{"csv_column": "...", "confidence": 0.0}}
  }},
  "status_map": {{
    "value": "Normalized Value"
  }},
  "unmapped_columns": []
}}
"""

    print("\n[CORVUS] Analyzing CSV structure...\n")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=4096,
            top_p=0.1,
            extra_body={"chat_template_kwargs": {"thinking": False}},
        )

        if not response or not response.choices:
            raise ValueError("Empty response from LLM")

        message = response.choices[0].message
        raw = message.content

        if not raw or not raw.strip():
            reasoning = getattr(message, "reasoning_content", None) or ""
            if reasoning:
                print("[CORVUS] Using reasoning_content (message.content was empty)")
                json_start = reasoning.find("{")
                json_end = reasoning.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    raw = reasoning[json_start:json_end]

        if not raw or not raw.strip():
            print("[CORVUS] LLM returned no usable content or JSON.")
            raise ValueError("LLM returned no usable content")

        raw = raw.strip()

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("[CORVUS] JSON incomplete — attempting recovery...")
            last_brace = raw.rfind("}")
            if last_brace != -1:
                trimmed = raw[:last_brace + 1]
                try:
                    return json.loads(trimmed)
                except json.JSONDecodeError:
                    pass
            print("[CORVUS ERROR] Could not recover JSON")
            raise

    except Exception as e:
        print("\n[CORVUS ERROR]:")
        traceback.print_exc()
        raise


def display_and_confirm_mapping(proposal: dict, headers: list[str]) -> tuple[dict, dict]:
    """
    Display proposed mapping.
    Auto-accept high confidence fields.
    Prompt user on low confidence fields.
    Returns confirmed column_map and status_map.
    """
    mapping = proposal.get("mapping", {})
    status_map = proposal.get("status_map", {})
    unmapped = proposal.get("unmapped_columns", [])

    confirmed_column_map = {}
    auto_accepted = []
    needs_review = []

    print("=" * 60)
    print("PROPOSED COLUMN MAPPING")
    print("=" * 60)

    for field, info in mapping.items():
        csv_col = info.get("csv_column")
        confidence = info.get("confidence", 0.0)
        reasoning = info.get("reasoning", "")

        if confidence >= CONFIDENCE_THRESHOLD:
            auto_accepted.append((field, csv_col, confidence, reasoning))
        else:
            needs_review.append((field, csv_col, confidence, reasoning))

    print(f"\n✅  AUTO-ACCEPTED (confidence ≥ {CONFIDENCE_THRESHOLD}):\n")
    for field, csv_col, confidence, _ in auto_accepted:
        if csv_col:
            print(f"  {field:<22} ← '{csv_col}' ({int(confidence*100)}%)")
            confirmed_column_map[field] = csv_col
        else:
            print(f"  {field:<22} ← no match found (will use default)")
            confirmed_column_map[field] = None

    if needs_review:
        print(f"\n⚠️   NEEDS YOUR REVIEW (confidence < {CONFIDENCE_THRESHOLD}):\n")
        print(f"Available CSV columns: {headers}\n")

        for field, csv_col, confidence, reasoning in needs_review:

            # no match at all — skip silently, use default
            if not csv_col:
                continue

            # low confidence match exists — prompt to confirm
            print(f"  Field: {field}")
            print(f"  Description: {CORVUS_SCHEMA.get(field, '')}")
            print(f"  Best guess: '{csv_col}' ({int(confidence*100)}% confidence)")
            if reasoning:
                print(f"  Reasoning: {reasoning}")

            while True:
                user_input = input(
                    f"\n  Accept '{csv_col}'? Press Enter to accept, "
                    f"or type correct CSV column name: "
                ).strip()
                if not user_input:
                    confirmed_column_map[field] = csv_col
                    break
                elif user_input in headers:
                    confirmed_column_map[field] = user_input
                    break
                else:
                    print(f"  ⚠️  '{user_input}' not in CSV. Available: {headers}")

            print()

    if status_map:
        print("\n📋  STATUS NORMALIZATION:\n")
        for their_val, our_val in status_map.items():
            print(f"  '{their_val}' → '{our_val}'")
        confirm = input(
            "\n  Accept status mapping? (Enter=yes, n=skip): "
        ).strip().lower()
        if confirm == "n":
            status_map = {}

    if unmapped:
        print(f"\n❓  UNMAPPED COLUMNS (not used by Corvus): {unmapped}")

    print("\n" + "=" * 60)

    return confirmed_column_map, status_map


def save_mapping_to_onboarding(
    onboarding_path: str,
    onboarding: dict,
    column_map: dict,
    status_map: dict,
    file_path: str,
    fingerprint: str
):
    """Write confirmed mapping back to onboarding.yaml."""
    clean_map = {k: v for k, v in column_map.items() if v is not None}

    onboarding["csv_connector"] = {
        "file_path": file_path,
        "mapping_fingerprint": fingerprint,
        "column_map": clean_map,
        "status_map": status_map if status_map else {}
    }

    with open(onboarding_path, "w") as f:
        yaml.dump(onboarding, f, default_flow_style=False, sort_keys=False)

    print(f"\n[CORVUS] Mapping saved → {onboarding_path}")
    print(f"[CORVUS] Fingerprint: {fingerprint}")
    print(f"[CORVUS] Next run will skip LLM mapping call.\n")


def check_existing_mapping(
    onboarding: dict,
    file_path: str,
    current_fingerprint: str,
    current_headers: list[str]
) -> bool:
    """
    Check if a valid cached mapping exists.
    Returns True if we can skip LLM call.
    """
    csv_config = onboarding.get("csv_connector", {})
    saved_fingerprint = csv_config.get("mapping_fingerprint")
    column_map = csv_config.get("column_map", {})

    if not saved_fingerprint or not column_map:
        return False

    if saved_fingerprint != current_fingerprint:
        print("[CORVUS] CSV structure has changed since last mapping — remapping...\n")
        return False

    is_valid, missing = verify_mapping_still_valid(column_map, current_headers)
    if not is_valid:
        print("[CORVUS] Mapped columns missing from CSV — remapping...")
        for m in missing:
            print(m)
        print()
        return False

    print("[CORVUS] Existing mapping is current — skipping LLM call.\n")
    return True


def run(csv_path: str, onboarding_path: str, force: bool = False):
    """Main entry point."""
    if not os.path.exists(csv_path):
        print(f"[CORVUS] File not found: {csv_path}")
        sys.exit(1)

    config_path = os.path.join(_AGENT_ROOT, "config", "config.yaml")
    config = load_config(config_path)
    onboarding = load_onboarding(onboarding_path)

    print(f"\n[CORVUS] Reading: {csv_path}")
    headers, sample_rows = read_csv_sample(csv_path)
    print(f"[CORVUS] Found {len(headers)} columns: {headers}")

    fingerprint = get_csv_fingerprint(csv_path)

    if not force and check_existing_mapping(onboarding, csv_path, fingerprint, headers):
        print("[CORVUS] Mapping is current. Use --force to remap.")
        return

    if force:
        print("[CORVUS] Force flag set — remapping regardless of cache.\n")

    proposal = propose_mapping_with_llm(headers, sample_rows, config)
    column_map, status_map = display_and_confirm_mapping(proposal, headers)

    save_mapping_to_onboarding(
        onboarding_path=onboarding_path,
        onboarding=onboarding,
        column_map=column_map,
        status_map=status_map,
        file_path=csv_path,
        fingerprint=fingerprint
    )

    print("[CORVUS] Ready. Run: python agents/debrief/src/main.py --csv <path>")


if __name__ == "__main__":
    default_onboarding = os.path.join(_AGENT_ROOT, "config", "onboarding.yaml")
    parser = argparse.ArgumentParser(description="Corvus CSV Column Mapper")
    parser.add_argument("csv_path", help="Path to customer CSV file")
    parser.add_argument(
        "--onboarding",
        default=default_onboarding,
        help="Path to onboarding config",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force remapping even if a valid mapping exists"
    )
    args = parser.parse_args()
    run(args.csv_path, args.onboarding, force=args.force)
