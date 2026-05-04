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
    python agents/debrief/src/tools/map_csv.py shared/data/input.csv --yes --dry-run
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
from intake.mapping_registry import (
    REQUIRED_WORK_ORDER_FIELDS,
    WORK_ORDER_SCHEMA,
    normalize_name,
    resolve_header,
)
from intake.schema_mapper import (
    propose_mapping_with_heuristics,
    validate_mapping as validate_schema_mapping,
)
from intake.source_classifier import classify_rows
from utils.config import load_config, load_onboarding


CORVUS_SCHEMA = WORK_ORDER_SCHEMA
REQUIRED_FIELDS = REQUIRED_WORK_ORDER_FIELDS
CONFIDENCE_THRESHOLD = 0.85


def get_csv_fingerprint(file_path: str) -> str:
    """
    Hash sorted normalized headers.
    Detects schema changes and column reorders without remapping for new data.
    """
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("CSV file is empty")

    sorted_headers = sorted(normalize_name(h) for h in headers)
    fingerprint_input = "|".join(sorted_headers)
    return hashlib.md5(fingerprint_input.encode()).hexdigest()[:12]


def verify_mapping_still_valid(
    column_map: dict,
    current_headers: list[str]
) -> tuple[bool, list[str]]:
    """
    Before skipping LLM call, verify mapped columns
    still exist in the current CSV.
    """
    normalized = {normalize_name(h) for h in current_headers}
    missing = []
    for corvus_field, csv_col in column_map.items():
        if csv_col and normalize_name(csv_col) not in normalized:
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


def merge_mapping_proposals(base: dict, override: dict, fields: list[str]) -> dict:
    """Merge LLM guesses into a heuristic proposal for unresolved fields."""
    merged = {
        "mapping": dict(base.get("mapping", {})),
        "status_map": override.get("status_map") or base.get("status_map", {}),
        "unmapped_columns": override.get("unmapped_columns", []),
    }
    override_mapping = override.get("mapping", {})
    for field in fields:
        if field in override_mapping:
            merged["mapping"][field] = override_mapping[field]
    return merged


def propose_mapping_with_llm(
    headers: list[str],
    sample_rows: list[dict],
    config: dict,
    fields_to_map: list[str] | None = None,
    existing_mapping: dict | None = None,
) -> dict:
    """
    Ask LLM to propose column mapping from customer CSV to Corvus schema.
    Returns mapping with confidence scores.
    """
    agent_config = config.get("agents", {})
    api_key = agent_config.get("api_key")
    if not api_key:
        raise EnvironmentError(
            "Missing LLM API key for unresolved CSV mapping fields. "
            "Set NIM_API_KEY or provide the mapping manually."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=agent_config.get("base_url")
    )
    model = agent_config.get("model", "moonshotai/kimi-k2.5")
    fields_to_map = fields_to_map or list(CORVUS_SCHEMA)
    schema = {field: CORVUS_SCHEMA[field] for field in fields_to_map}

    schema_description = "\n".join(
        f"{field}: {desc}" for field, desc in schema.items()
    )
    sample_text = json.dumps(sample_rows, indent=2)
    existing_text = json.dumps(existing_mapping or {}, indent=2)
    mapping_template = ",\n".join(
        f'    "{field}": {{"csv_column": null, "confidence": 0.0}}'
        for field in fields_to_map
    )

    prompt = f"""
You are a data mapping assistant.
You MUST output valid JSON only.
Do NOT output explanations.
Do NOT output reasoning.
Do NOT output markdown.
Do NOT think step by step.

FIELDS TO MAP:
{schema_description}

ALREADY MAPPED FIELDS:
{existing_text}

CSV HEADERS:
{headers}

SAMPLE ROWS:
{sample_text}

Return JSON in this format:
{{
  "mapping": {{
{mapping_template}
  }},
  "status_map": {{
    "value": "Normalized Value"
  }},
  "unmapped_columns": []
}}
"""

    print("\n[CORVUS] Analyzing CSV structure...\n")

    try:
        request = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 4096,
            "top_p": 0.1,
            "extra_body": {"chat_template_kwargs": {"thinking": False}},
            "response_format": {"type": "json_object"},
        }
        try:
            response = client.chat.completions.create(**request)
        except TypeError:
            request.pop("response_format", None)
            response = client.chat.completions.create(**request)
        except Exception as exc:
            if "response_format" not in str(exc):
                raise
            request.pop("response_format", None)
            response = client.chat.completions.create(**request)

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


def validate_mapping(
    column_map: dict,
    status_map: dict,
    headers: list[str],
    require_required: bool = True,
) -> tuple[dict, dict, list[str]]:
    """Normalize mapped headers and report invalid or missing required fields."""
    required = REQUIRED_FIELDS if require_required else []
    return validate_schema_mapping(
        column_map,
        status_map,
        headers,
        required_fields=required,
        schema=CORVUS_SCHEMA,
    )


def display_and_confirm_mapping(
    proposal: dict,
    headers: list[str],
    yes: bool = False,
) -> tuple[dict, dict]:
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

    for field in CORVUS_SCHEMA:
        info = mapping.get(field, {})
        csv_col = info.get("csv_column")
        csv_col = resolve_header(csv_col, headers) or csv_col
        confidence = info.get("confidence", 0.0)
        reasoning = info.get("reasoning", "")

        if csv_col and not resolve_header(csv_col, headers):
            needs_review.append((field, csv_col, 0.0, "Column was not found in CSV headers."))
        elif confidence >= CONFIDENCE_THRESHOLD:
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

            if yes:
                actual_header = resolve_header(csv_col, headers)
                if actual_header:
                    confirmed_column_map[field] = actual_header
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
                else:
                    actual_header = resolve_header(user_input, headers)
                    if actual_header:
                        confirmed_column_map[field] = actual_header
                        break
                    print(f"  ⚠️  '{user_input}' not in CSV. Available: {headers}")

            print()

    if status_map:
        print("\n📋  STATUS NORMALIZATION:\n")
        for their_val, our_val in status_map.items():
            print(f"  '{their_val}' → '{our_val}'")
        if not yes:
            confirm = input(
                "\n  Accept status mapping? (Enter=yes, n=skip): "
            ).strip().lower()
            if confirm == "n":
                status_map = {}

    if unmapped:
        print(f"\n❓  UNMAPPED COLUMNS (not used by Corvus): {unmapped}")

    print("\n" + "=" * 60)

    clean_map, clean_status_map, issues = validate_mapping(
        confirmed_column_map,
        status_map,
        headers,
        require_required=True,
    )
    if issues:
        print("\n[CORVUS] Mapping validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        if any(issue.startswith("Required field") for issue in issues):
            raise ValueError("Cannot save CSV mapping without required fields.")

    return clean_map, clean_status_map


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


def build_mapping_proposal(
    headers: list[str],
    sample_rows: list[dict],
    config: dict,
) -> dict:
    """Build a mapping proposal using heuristics first, then LLM for gaps."""
    proposal = propose_mapping_with_heuristics(headers, source_type="work_order")
    unresolved = [
        field for field, info in proposal["mapping"].items()
        if not info.get("csv_column")
    ]

    if not unresolved:
        print("[CORVUS] Heuristic mapper resolved all schema fields.\n")
        return proposal

    print(
        "[CORVUS] Heuristic mapper resolved "
        f"{len(CORVUS_SCHEMA) - len(unresolved)} of {len(CORVUS_SCHEMA)} fields."
    )

    try:
        llm_proposal = propose_mapping_with_llm(
            headers,
            sample_rows,
            config,
            fields_to_map=unresolved,
            existing_mapping={
                field: info["csv_column"]
                for field, info in proposal["mapping"].items()
                if info.get("csv_column")
            },
        )
    except EnvironmentError:
        required_missing = [f for f in REQUIRED_FIELDS if f in unresolved]
        if required_missing:
            raise
        print("[CORVUS] No LLM API key found; using heuristic mapping only.\n")
        return proposal

    return merge_mapping_proposals(proposal, llm_proposal, unresolved)


def run(
    csv_path: str,
    onboarding_path: str,
    force: bool = False,
    yes: bool = False,
    dry_run: bool = False,
    output_path: str | None = None,
):
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
    classification = classify_rows(headers, sample_rows)
    print(
        "[CORVUS] Source classification: "
        f"{classification['source_type']} "
        f"({int(classification['confidence'] * 100)}% confidence)"
    )

    fingerprint = get_csv_fingerprint(csv_path)

    if not force and check_existing_mapping(onboarding, fingerprint, headers):
        print("[CORVUS] Mapping is current. Use --force to remap.")
        return

    if force:
        print("[CORVUS] Force flag set — remapping regardless of cache.\n")

    proposal = build_mapping_proposal(headers, sample_rows, config)
    column_map, status_map = display_and_confirm_mapping(
        proposal,
        headers,
        yes=yes,
    )

    preview = {
        "csv_connector": {
            "file_path": csv_path,
            "mapping_fingerprint": fingerprint,
            "column_map": column_map,
            "status_map": status_map if status_map else {},
        }
    }

    if dry_run:
        print("\n[CORVUS] Dry run: mapping preview follows.\n")
        print(yaml.dump(preview, default_flow_style=False, sort_keys=False))
        return

    if output_path:
        with open(output_path, "w") as f:
            yaml.dump(preview, f, default_flow_style=False, sort_keys=False)
        print(f"\n[CORVUS] Mapping preview saved → {output_path}")
        return
    else:
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
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Accept all valid proposed mappings without prompts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the proposed mapping without writing onboarding.yaml",
    )
    parser.add_argument(
        "--output",
        help="Write mapping preview YAML to this path instead of onboarding.yaml",
    )
    args = parser.parse_args()
    run(
        args.csv_path,
        args.onboarding,
        force=args.force,
        yes=args.yes,
        dry_run=args.dry_run,
        output_path=args.output,
    )
