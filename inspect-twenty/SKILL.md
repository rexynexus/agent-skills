---
name: inspect-twenty
description: Inspect a Twenty CRM object type by querying the live API. Use when investigating Twenty data structure, field availability, data quality, or record counts.
argument-hint: "[object-name]"
disable-model-invocation: true
---

Inspect a Twenty CRM object by running the bundled analysis script, then interpret and contextualize the results.

The script queries **both** API surfaces:
- **REST Metadata API** (`/rest/metadata/objects`, `/rest/metadata/fields`) for authoritative field definitions (type, label, required, relations, custom vs standard)
- **REST Data API** (`/rest/{object}`) for actual records (sample values, null rates, CURRENCY decoding, anomaly detection)

It also cross-references both sources to detect **schema drift** (fields that exist in metadata but not in data, or vice versa; type mismatches between declared and observed).

## Step 1: Run the inspection script

```bash
python Skills/inspect-twenty/scripts/inspect.py $ARGUMENTS
```

If the script is not found at that path, search for `inspect-twenty/scripts/inspect.py` in the workspace and additional directories.

### Flags

- `--metadata-only` - Schema definitions only, no record data (faster, no pagination)
- `--data-only` - Record analysis only, skip metadata (if metadata endpoint is unavailable)
- `--env-file PATH` - Explicit path to `.env` (default: searches upward from cwd)

## Step 2: Interpret the results

After the script runs, review its output and add context:

1. **Cross-reference with design.md** if an Artifacts folder exists. Note mismatches between the planned schema and the live API.
2. **Explain CURRENCY field semantics** in business terms (e.g. `contractValue` is the original signed amount, `currentContractValue` is the live ceiling after amendments).
3. **Assess relation usefulness** based on population rates. If a relation has 0 populated records, say so explicitly.
4. **Contextualize anomalies** - what each one means and whether it matters for the revenue dashboard.
5. **Interpret schema drift** - are missing fields expected (system fields, computed fields) or concerning (data model changes)?
6. **Recommend next steps** if any fields or patterns warrant further investigation.

## Step 3: If the script fails

- Missing `httpx`: run `pip install httpx` and retry
- Auth errors: check `.env` for `TWENTY_API_KEY` and `TWENTY_BASE_URL`
- Object not found: the script tries singular/plural variants and lists available objects
- Metadata 403/404: the metadata endpoint may require different API permissions. Use `--data-only` as fallback.

## What the script does NOT cover

- **GraphQL core API** (`/graphql`): Could surface additional computed fields or deeper relation traversals not visible via REST. The REST metadata covers field definitions, but GraphQL may expose query capabilities (filtering, aggregation) that REST lacks. If the inspection reveals gaps, suggest a follow-up GraphQL introspection.
- **Write operations**: The script is strictly read-only.
