#!/usr/bin/env python3
"""
Inspect a Twenty CRM object type via both the REST data API and the
REST metadata API.

- Metadata API (/rest/metadata/objects, /rest/metadata/fields) provides
  authoritative field definitions: type, label, required, relation targets.
- Data API (/rest/{object}) provides actual record data for sample values,
  null rates, CURRENCY decoding, and anomaly detection.

Usage:
    python inspect.py <object-name> [--env-file PATH] [--metadata-only] [--data-only]

Requires: httpx
Optional: python-dotenv
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx not installed. Run: pip install httpx")

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_REQUEST_INTERVAL = 0.6
MAX_RETRIES = 5
RETRY_DELAY = 2.0
TIMEOUT = 30.0
BATCH_SIZE = 200
SPARSE_THRESHOLD = 0.80

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?")

# ---------------------------------------------------------------------------
# API helpers (mirrors patterns from api/sync/twenty.py)
# ---------------------------------------------------------------------------


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ElevateRevenueDashboard/InspectSkill",
    }


def _rate_limited_get(client, url, api_key, params=None, last_request_time_ref=None):
    """Single GET with rate limiting and retry logic. Returns response or None."""
    if last_request_time_ref is None:
        last_request_time_ref = [0.0]

    now = time.time()
    elapsed = now - last_request_time_ref[0]
    if last_request_time_ref[0] > 0 and elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

    resp = None
    for attempt in range(MAX_RETRIES):
        try:
            last_request_time_ref[0] = time.time()
            resp = client.get(url, headers=_headers(api_key), params=params)
        except httpx.RequestError as exc:
            print(f"WARN: Request error ({exc}), retry {attempt+1}/{MAX_RETRIES}", file=sys.stderr)
            time.sleep(RETRY_DELAY)
            continue

        if resp.status_code == 429:
            wait = RETRY_DELAY * (2 ** attempt)
            print(f"WARN: Rate limited, waiting {wait:.1f}s", file=sys.stderr)
            resp = None
            time.sleep(wait)
            continue
        break

    return resp


def fetch_all(client, api_key, base_url, object_name, timer=None):
    """Fetch all non-deleted records with cursor pagination."""
    if timer is None:
        timer = [0.0]
    url = f"{base_url}/{object_name}"
    params = {"limit": BATCH_SIZE}
    all_records = []

    while True:
        resp = _rate_limited_get(client, url, api_key, params, timer)

        if resp is None:
            print("ERROR: Exhausted retries fetching records", file=sys.stderr)
            break
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        body = resp.json()

        data = body.get("data", body)
        if isinstance(data, dict):
            records = data.get(object_name, [])
            if not records:
                singular = object_name.rstrip("s")
                records = data.get(singular, [])
            if not records:
                for v in data.values():
                    if isinstance(v, list):
                        records = v
                        break
        elif isinstance(data, list):
            records = data
        else:
            records = []

        all_records.extend(r for r in records if not r.get("deletedAt"))

        page_info = body.get("pageInfo", {})
        if page_info.get("hasNextPage") and page_info.get("endCursor"):
            params["starting_after"] = page_info["endCursor"]
        else:
            break

    return all_records


# ---------------------------------------------------------------------------
# Metadata API
# ---------------------------------------------------------------------------


def fetch_metadata_objects(client, api_key, base_url, timer=None):
    """Fetch all object definitions from /rest/metadata/objects."""
    if timer is None:
        timer = [0.0]
    all_objects = []
    params = {}

    while True:
        resp = _rate_limited_get(
            client, f"{base_url}/metadata/objects", api_key, params, timer
        )
        if resp is None or resp.status_code != 200:
            break
        body = resp.json()
        data = body.get("data", body)
        if isinstance(data, dict):
            objects = data.get("objects", [])
        elif isinstance(data, list):
            objects = data
        else:
            break
        all_objects.extend(objects)

        page_info = body.get("pageInfo", {})
        if page_info.get("hasNextPage") and page_info.get("endCursor"):
            params["starting_after"] = page_info["endCursor"]
        else:
            break

    return all_objects


def fetch_metadata_fields(client, api_key, base_url, timer=None):
    """Fetch all field definitions from /rest/metadata/fields.

    Returns all fields across all objects. The response is NOT grouped by
    object, so we group them by objectMetadataId.
    """
    if timer is None:
        timer = [0.0]
    all_fields = []
    params = {}

    while True:
        resp = _rate_limited_get(
            client, f"{base_url}/metadata/fields", api_key, params, timer
        )
        if resp is None or resp.status_code != 200:
            break
        body = resp.json()
        data = body.get("data", body)
        if isinstance(data, dict):
            fields = data.get("fields", [])
        elif isinstance(data, list):
            fields = data
        else:
            break
        all_fields.extend(fields)

        page_info = body.get("pageInfo", {})
        if page_info.get("hasNextPage") and page_info.get("endCursor"):
            params["starting_after"] = page_info["endCursor"]
        else:
            break

    return all_fields


def resolve_object_metadata(meta_objects, meta_fields, object_name):
    """Find the object definition and its fields from metadata.

    Returns (object_def, field_defs) or (None, []) if not found.
    object_name is matched against namePlural, nameSingular, and labelPlural
    (case-insensitive).
    """
    target = object_name.lower()
    obj_def = None
    for obj in meta_objects:
        candidates = [
            (obj.get("namePlural") or "").lower(),
            (obj.get("nameSingular") or "").lower(),
            (obj.get("labelPlural") or "").lower(),
            (obj.get("labelSingular") or "").lower(),
        ]
        if target in candidates:
            obj_def = obj
            break

    if obj_def is None:
        return None, []

    obj_id = obj_def.get("id")
    field_defs = [
        f for f in meta_fields
        if f.get("objectMetadataId") == obj_id
    ]
    return obj_def, field_defs


# ---------------------------------------------------------------------------
# Data analysis (from REST records)
# ---------------------------------------------------------------------------


def infer_type(value):
    """Infer a human-readable type string from a sample value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        if len(value) > 0 and isinstance(value[0], dict):
            return "relation[]"
        return "array"
    if isinstance(value, dict):
        if "amountMicros" in value or "currencyCode" in value:
            return "CURRENCY"
        if "primaryLinkUrl" in value or "secondaryLinks" in value:
            return "LINK"
        if "edges" in value:
            return "connection"
        return "object"
    if isinstance(value, str):
        if UUID_RE.match(value):
            return "uuid"
        if ISO_DATE_RE.match(value):
            return "datetime" if "T" in value else "date"
        return "string"
    return type(value).__name__


def is_empty(value):
    """Check if a value is null, empty string, empty list, or zero."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict):
        if "amountMicros" in value and value["amountMicros"] is None:
            return True
        if "edges" in value and len(value.get("edges", [])) == 0:
            return True
    return False


def analyze_fields(records):
    """Analyze all fields across all records."""
    if not records:
        return {"fields": {}, "record_count": 0}

    n = len(records)
    field_data = defaultdict(lambda: {
        "types": Counter(),
        "empty_count": 0,
        "sample": None,
        "all_values": [],
    })

    for record in records:
        for key, value in record.items():
            fd = field_data[key]
            fd["types"][infer_type(value)] += 1
            if is_empty(value):
                fd["empty_count"] += 1
            elif fd["sample"] is None:
                fd["sample"] = value
            fd["all_values"].append(value)

    fields = {}
    for name, fd in sorted(field_data.items()):
        primary_type = fd["types"].most_common(1)[0][0]
        if primary_type == "null" and len(fd["types"]) > 1:
            primary_type = fd["types"].most_common(2)[1][0]

        empty_rate = fd["empty_count"] / n
        sample = fd["sample"]
        sample_str = _format_sample(sample)

        fields[name] = {
            "type": primary_type,
            "empty_rate": empty_rate,
            "sparse": empty_rate > SPARSE_THRESHOLD,
            "sample": sample_str,
            "raw_sample": sample,
            "all_values": fd["all_values"],
        }

    return {"fields": fields, "record_count": n}


def _format_sample(value, max_len=80):
    if value is None:
        return "(all null)"
    if isinstance(value, dict):
        if "amountMicros" in value:
            micros = value.get("amountMicros")
            currency = value.get("currencyCode", "???")
            if micros is not None:
                return f"${micros / 1_000_000:,.2f} {currency}"
            return f"null {currency}"
        s = json.dumps(value)
    elif isinstance(value, list):
        s = json.dumps(value)
    else:
        s = str(value)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


# ---------------------------------------------------------------------------
# CURRENCY analysis
# ---------------------------------------------------------------------------


def analyze_currency_fields(fields):
    results = []
    for name, info in fields.items():
        if info["type"] != "CURRENCY":
            continue
        currencies = Counter()
        values = []
        for v in info["all_values"]:
            if isinstance(v, dict):
                code = v.get("currencyCode")
                micros = v.get("amountMicros")
                if code:
                    currencies[code] += 1
                if micros is not None:
                    values.append(micros / 1_000_000)
        results.append({
            "name": name,
            "currencies": dict(currencies),
            "non_null_count": len(values),
            "sample_display": info["sample"],
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        })
    return results


# ---------------------------------------------------------------------------
# Relation analysis
# ---------------------------------------------------------------------------


def analyze_relations(fields):
    results = []
    for name, info in fields.items():
        if info["type"] not in ("relation[]", "connection"):
            continue
        populated = 0
        total_children = 0
        for v in info["all_values"]:
            if isinstance(v, list) and len(v) > 0:
                populated += 1
                total_children += len(v)
            elif isinstance(v, dict) and len(v.get("edges", [])) > 0:
                populated += 1
                total_children += len(v["edges"])
        results.append({
            "name": name,
            "type": info["type"],
            "populated_records": populated,
            "total_children": total_children,
            "empty_rate": info["empty_rate"],
        })
    return results


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------


def detect_anomalies(records, fields):
    anomalies = []

    # CURRENCY computed field consistency
    cv_field = tav_field = ccv_field = None
    for name in fields:
        lower = name.lower()
        if lower == "contractvalue":
            cv_field = name
        elif lower == "totalamendmentvalue":
            tav_field = name
        elif lower == "currentcontractvalue":
            ccv_field = name

    if cv_field and tav_field and ccv_field:
        for i, r in enumerate(records):
            cv = _extract_micros(r.get(cv_field))
            tav = _extract_micros(r.get(tav_field))
            ccv = _extract_micros(r.get(ccv_field))
            if cv is not None and tav is not None and ccv is not None:
                expected = cv + tav
                if abs(expected - ccv) > 1:
                    rname = r.get("name", r.get("id", f"record-{i}"))
                    anomalies.append(
                        f"**{rname}**: contractValue ({cv/1e6:,.2f}) + "
                        f"totalAmendmentValue ({tav/1e6:,.2f}) = "
                        f"{expected/1e6:,.2f}, but currentContractValue = "
                        f"{ccv/1e6:,.2f}"
                    )

    # Negative CURRENCY values
    for name, info in fields.items():
        if info["type"] != "CURRENCY":
            continue
        negatives = sum(
            1 for v in info["all_values"]
            if isinstance(v, dict) and (v.get("amountMicros") or 0) < 0
        )
        if negatives > 0:
            anomalies.append(
                f"**{name}**: {negatives} record(s) have negative currency values"
            )

    # Future dates in non-range fields
    today = time.strftime("%Y-%m-%d")
    for name, info in fields.items():
        if info["type"] not in ("date", "datetime"):
            continue
        if any(kw in name.lower() for kw in ("end", "expir", "deadline", "target")):
            continue
        future_count = sum(
            1 for v in info["all_values"]
            if isinstance(v, str) and v > today
        )
        if future_count > 0:
            anomalies.append(
                f"**{name}**: {future_count} record(s) have future dates"
            )

    # UUID fields all identical (default/placeholder)
    for name, info in fields.items():
        if info["type"] != "uuid":
            continue
        non_null = [v for v in info["all_values"] if v is not None]
        if len(non_null) > 5 and len(set(non_null)) == 1:
            anomalies.append(
                f"**{name}**: All {len(non_null)} non-null values are identical "
                f"({non_null[0]}) - possible default/placeholder"
            )

    # Fields in data but missing from metadata (schema drift)
    # This is populated by the caller if metadata is available
    return anomalies


def _extract_micros(value):
    if isinstance(value, dict):
        return value.get("amountMicros")
    return None


# ---------------------------------------------------------------------------
# Schema drift detection
# ---------------------------------------------------------------------------


def detect_schema_drift(data_fields, meta_field_defs):
    """Compare fields seen in REST data vs metadata definitions.

    Returns list of drift findings.
    """
    drift = []

    meta_names = {}
    for f in meta_field_defs:
        api_name = f.get("name", "")
        if api_name:
            meta_names[api_name] = f

    data_names = set(data_fields.keys())
    meta_name_set = set(meta_names.keys())

    # Fields in data but not in metadata
    data_only = data_names - meta_name_set
    # Exclude system fields that may not appear in metadata
    system_fields = {"id", "createdAt", "updatedAt", "deletedAt", "createdBy", "updatedBy"}
    data_only -= system_fields
    if data_only:
        drift.append(
            f"Fields in REST data but not in metadata: {', '.join(f'`{n}`' for n in sorted(data_only))}"
        )

    # Fields in metadata but not in data
    meta_only = meta_name_set - data_names
    # Relations and computed fields may not appear in flat REST response
    meta_only_non_relation = []
    for n in meta_only:
        fdef = meta_names[n]
        ftype = (fdef.get("type") or "").upper()
        if ftype != "RELATION":
            meta_only_non_relation.append(n)
    if meta_only_non_relation:
        drift.append(
            f"Fields in metadata but missing from REST data: {', '.join(f'`{n}`' for n in sorted(meta_only_non_relation))}"
        )

    # Type mismatches between inferred type and metadata type
    for name in data_names & meta_name_set:
        meta_type = (meta_names[name].get("type") or "").upper()
        inferred = data_fields[name]["type"]
        # Map metadata types to our inferred types for comparison
        type_map = {
            "TEXT": "string",
            "UUID": "uuid",
            "DATE_TIME": "datetime",
            "DATE": "date",
            "BOOLEAN": "boolean",
            "NUMBER": "number",
            "CURRENCY": "CURRENCY",
            "LINK": "LINK",
            "LINKS": "LINK",
            "RELATION": "connection",
            "FULL_NAME": "object",
            "EMAILS": "object",
            "PHONES": "object",
            "ADDRESS": "object",
            "RATING": "string",
            "SELECT": "string",
            "MULTI_SELECT": "string",
            "RICH_TEXT": "string",
            "RAW_JSON": "object",
            "ACTOR": "object",
            "ARRAY": "array",
            "TS_VECTOR": "string",
        }
        expected = type_map.get(meta_type)
        if expected and expected != inferred and inferred != "null":
            drift.append(
                f"`{name}`: metadata says {meta_type}, data looks like {inferred}"
            )

    return drift


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------


def render_markdown(
    object_name,
    obj_def,
    meta_field_defs,
    records,
    analysis,
    currency_info,
    relation_info,
    anomalies,
    schema_drift,
    metadata_available,
):
    fields = analysis["fields"] if analysis else {}
    n = analysis["record_count"] if analysis else 0

    sparse_fields = [name for name, f in fields.items() if f.get("sparse")]
    currency_names = [c["name"] for c in currency_info]
    relation_names = [r["name"] for r in relation_info]

    lines = []
    lines.append(f"# Twenty Object Inspection: `{object_name}`\n")

    # --- Summary table ---
    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Object | `{object_name}` |")

    if obj_def:
        lines.append(f"| Label | {obj_def.get('labelPlural', 'n/a')} |")
        lines.append(f"| Singular | {obj_def.get('nameSingular', 'n/a')} |")
        is_custom = obj_def.get("isCustom", False)
        lines.append(f"| Custom object | {'Yes' if is_custom else 'No (standard)'} |")

    lines.append(f"| Records | {n:,} |")
    total_fields = len(meta_field_defs) if meta_field_defs else len(fields)
    lines.append(f"| Fields (metadata) | {len(meta_field_defs) if meta_field_defs else 'n/a'} |")
    lines.append(f"| Fields (in data) | {len(fields)} |")
    lines.append(f"| Sparse (>{SPARSE_THRESHOLD:.0%} null) | {', '.join(f'`{s}`' for s in sparse_fields) or 'none'} |")
    lines.append(f"| CURRENCY fields | {', '.join(f'`{c}`' for c in currency_names) or 'none'} |")
    lines.append(f"| Relations | {', '.join(f'`{r}`' for r in relation_names) or 'none'} |")
    lines.append(f"| Data source | REST (`/rest/{object_name}`) |")
    lines.append(f"| Schema source | {'REST metadata (`/rest/metadata/fields`)' if metadata_available else 'Inferred from data only'} |")
    lines.append("")

    # --- Metadata field definitions ---
    if meta_field_defs:
        lines.append("## Schema (from Metadata API)\n")
        lines.append("| Field | Type | Label | Required | Description |")
        lines.append("|-------|------|-------|----------|-------------|")
        for f in sorted(meta_field_defs, key=lambda x: x.get("name", "")):
            fname = f.get("name", "?")
            ftype = f.get("type", "?")
            flabel = f.get("label", "")
            freq = "Yes" if f.get("isNullable") is False else ""
            fdesc = (f.get("description") or "").replace("|", "\\|")
            if len(fdesc) > 60:
                fdesc = fdesc[:57] + "..."
            lines.append(f"| `{fname}` | {ftype} | {flabel} | {freq} | {fdesc} |")

        # Relation fields from metadata
        relation_defs = [f for f in meta_field_defs if (f.get("type") or "").upper() == "RELATION"]
        if relation_defs:
            lines.append("")
            lines.append("### Relation Fields (Metadata)\n")
            lines.append("| Field | Target object | Relation type |")
            lines.append("|-------|---------------|---------------|")
            for f in relation_defs:
                fname = f.get("name", "?")
                rel_meta = f.get("relationDefinition") or {}
                target = rel_meta.get("targetObjectMetadata", {}).get("namePlural", "?")
                rel_type = rel_meta.get("type", rel_meta.get("direction", "?"))
                lines.append(f"| `{fname}` | `{target}` | {rel_type} |")
        lines.append("")

    # --- Field inventory from data ---
    if fields:
        lines.append("## Field Inventory (from Data)\n")
        lines.append("| Field | Inferred type | Empty % | Sample |")
        lines.append("|-------|---------------|---------|--------|")
        for name, f in fields.items():
            empty_pct = f"{f['empty_rate']:.0%}"
            sample = f["sample"].replace("|", "\\|") if f["sample"] else ""
            flag = " **SPARSE**" if f["sparse"] else ""
            lines.append(f"| `{name}` | {f['type']} | {empty_pct}{flag} | {sample} |")
        lines.append("")

    # --- CURRENCY fields ---
    if currency_info:
        lines.append("## CURRENCY Fields\n")
        for c in currency_info:
            lines.append(f"### `{c['name']}`\n")
            lines.append(f"- Currencies: {c['currencies']}")
            lines.append(f"- Non-null values: {c['non_null_count']} of {n}")
            if c["min"] is not None:
                lines.append(f"- Range: ${c['min']:,.2f} to ${c['max']:,.2f}")
            lines.append(f"- Sample: {c['sample_display']}")
            lines.append("")

    # --- Relations from data ---
    if relation_info:
        lines.append("## Relations (from Data)\n")
        lines.append("| Field | Type | Populated | Total children | Empty % |")
        lines.append("|-------|------|-----------|----------------|---------|")
        for r in relation_info:
            lines.append(
                f"| `{r['name']}` | {r['type']} | {r['populated_records']}/{n} "
                f"| {r['total_children']} | {r['empty_rate']:.0%} |"
            )
        lines.append("")

    # --- Schema drift ---
    if schema_drift:
        lines.append("## Schema Drift (Metadata vs Data)\n")
        for d in schema_drift:
            lines.append(f"- {d}")
        lines.append("")

    # --- Anomalies ---
    lines.append("## Data Anomalies\n")
    if anomalies:
        for a in anomalies:
            lines.append(f"- {a}")
    else:
        lines.append("No anomalies detected.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Inspect a Twenty CRM object via REST data + metadata APIs"
    )
    parser.add_argument("object", help="Object name (e.g. contracts, opportunities)")
    parser.add_argument(
        "--env-file", default=None,
        help="Path to .env file (default: search upward from cwd)",
    )
    parser.add_argument(
        "--metadata-only", action="store_true",
        help="Only fetch metadata schema, skip record data",
    )
    parser.add_argument(
        "--data-only", action="store_true",
        help="Only fetch record data, skip metadata",
    )
    args = parser.parse_args()

    # Load env
    env_file = args.env_file
    if env_file is None:
        p = Path.cwd()
        while p != p.parent:
            candidate = p / ".env"
            if candidate.exists():
                env_file = str(candidate)
                break
            p = p.parent

    if env_file and load_dotenv:
        load_dotenv(env_file)
    elif env_file:
        for line in Path(env_file).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    api_key = os.environ.get("TWENTY_API_KEY")
    base_url = os.environ.get("TWENTY_BASE_URL") or os.environ.get("TWENTY_API_URL")

    if not api_key or not base_url:
        sys.exit("ERROR: TWENTY_API_KEY and TWENTY_BASE_URL must be set (via .env or environment)")

    base_url = base_url.rstrip("/")
    object_name = args.object.strip().lower()
    timer = [0.0]

    with httpx.Client(timeout=TIMEOUT) as client:

        # ----- Phase 1: Metadata -----
        obj_def = None
        meta_field_defs = []
        metadata_available = False

        if not args.data_only:
            print("Fetching metadata...", file=sys.stderr)
            meta_objects = fetch_metadata_objects(client, api_key, base_url, timer)
            meta_fields = fetch_metadata_fields(client, api_key, base_url, timer)

            if meta_objects:
                obj_def, meta_field_defs = resolve_object_metadata(
                    meta_objects, meta_fields, object_name
                )
                metadata_available = True

                if obj_def is None:
                    # Try alternate form
                    alt = object_name + "s" if not object_name.endswith("s") else object_name.rstrip("s")
                    obj_def, meta_field_defs = resolve_object_metadata(
                        meta_objects, meta_fields, alt
                    )
                    if obj_def:
                        object_name = alt

                if obj_def:
                    print(
                        f"  Found: {obj_def.get('labelPlural', object_name)} "
                        f"({len(meta_field_defs)} fields in metadata)",
                        file=sys.stderr,
                    )
                else:
                    print(f"  Object '{object_name}' not found in metadata", file=sys.stderr)
                    # List available objects for suggestion
                    available = sorted(
                        (o.get("namePlural") or o.get("nameSingular") or "?")
                        for o in meta_objects
                        if not o.get("isSystem", False)
                    )
                    if available:
                        print(f"  Available objects: {', '.join(available)}", file=sys.stderr)
            else:
                print("  Could not fetch metadata (may require different permissions)", file=sys.stderr)

        # If metadata-only, render and exit
        if args.metadata_only:
            report = render_markdown(
                object_name, obj_def, meta_field_defs,
                [], {"fields": {}, "record_count": 0},
                [], [], [], [], metadata_available,
            )
            print(report)
            return

        # ----- Phase 2: Record data -----
        print("Fetching records...", file=sys.stderr)
        records = fetch_all(client, api_key, base_url, object_name, timer)

        if records is None:
            alt = object_name + "s" if not object_name.endswith("s") else object_name.rstrip("s")
            print(f"  '{object_name}' not found, trying '{alt}'...", file=sys.stderr)
            records = fetch_all(client, api_key, base_url, alt, timer)
            if records is not None:
                object_name = alt

        if records is None:
            if not metadata_available:
                available = [
                    o.get("namePlural") or o.get("nameSingular") or "?"
                    for o in fetch_metadata_objects(client, api_key, base_url, timer)
                ]
            print(f"\nERROR: Object '{object_name}' not found via REST API.\n", file=sys.stderr)
            if obj_def:
                # We have metadata but no REST endpoint
                print("  Object exists in metadata but has no REST data endpoint.", file=sys.stderr)
                print("  Rendering metadata-only report.\n", file=sys.stderr)
                report = render_markdown(
                    object_name, obj_def, meta_field_defs,
                    [], {"fields": {}, "record_count": 0},
                    [], [], [], [], metadata_available,
                )
                print(report)
                return
            sys.exit(1)

        print(f"  Fetched {len(records)} records", file=sys.stderr)

    if not records and not meta_field_defs:
        print(f"# Twenty Object Inspection: `{object_name}`\n")
        print("Object exists but contains **0 records** and no metadata was found.")
        return

    # ----- Phase 3: Analysis -----
    analysis = analyze_fields(records) if records else {"fields": {}, "record_count": 0}
    currency_info = analyze_currency_fields(analysis["fields"])
    relation_info = analyze_relations(analysis["fields"])
    anomalies = detect_anomalies(records or [], analysis["fields"])

    schema_drift = []
    if meta_field_defs and analysis["fields"]:
        schema_drift = detect_schema_drift(analysis["fields"], meta_field_defs)

    # ----- Phase 4: Output -----
    report = render_markdown(
        object_name, obj_def, meta_field_defs,
        records, analysis, currency_info, relation_info,
        anomalies, schema_drift, metadata_available,
    )
    print(report)


if __name__ == "__main__":
    main()
