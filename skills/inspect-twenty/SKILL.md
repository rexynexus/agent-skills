---
name: inspect-twenty
description: Inspect a Twenty CRM object type by querying the live API. Use when investigating Twenty data structure, field availability, data quality, or record counts.
argument-hint: "[object-name]"
---

Inspect a Twenty CRM object by running the bundled analysis script, then interpret and contextualize the results.

The script queries **both** API surfaces:
- **REST Metadata API** (`/rest/metadata/objects`, which returns field definitions inline on each object) for authoritative field definitions (type, label, required, system flag, relation type and join column). Current Twenty versions do not return `isCustom` or relation target objects through this endpoint.
- **REST Data API** (`/rest/{plural}`) for actual records (sample values, null rates, CURRENCY decoding, anomaly detection). Records also carry relation join-column ids (e.g. `messageThreadId`) as scalars; the `depth` parameter (0/1) controls whether related records are nested.

It also cross-references both sources to detect **schema drift** (fields that exist in metadata but not in data, or vice versa; type mismatches between declared and observed).

## Step 1: Run the inspection script

```bash
python <base-directory>/scripts/inspect_twenty.py $ARGUMENTS
```

`<base-directory>` is the skill's own directory, provided by the skill invocation as "Base directory for this skill: <path>". If no base directory is given, search for `inspect-twenty/scripts/inspect_twenty.py` in the workspace and additional directories.

### Flags

- `--metadata-only` - Schema definitions only, no record data (faster, no pagination)
- `--data-only` - Record analysis only, skip metadata (if metadata endpoint is unavailable)
- `--env-file PATH` - Explicit path to `.env` (default: searches upward from cwd)
- `--max-records N` - Cap on records fetched for analysis (default: 1000). Large objects (e.g. `message`, 300k+ records on this instance) would otherwise take 40+ minutes to paginate; when the cap is hit the report labels the analysis as a partial sample of the first N records and shows the true total.

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
- Object not found: the script tries singular/plural variants and lists available objects. The `/rest/metadata/objects` list is NOT exhaustive - objects referenced by associations (e.g. `messageChannel`, referenced by `messageChannelMessageAssociation`) can be absent from the list and from the REST data API even though their ids appear in other objects' records. Before concluding an object does not exist, cross-check with a GraphQL `__schema` type-name scan (see below).
- Metadata 403/404: the metadata endpoint may require different API permissions. Use `--data-only` as fallback.

## What the script does NOT cover

- **GraphQL core API**: The endpoint lives at the host root, NOT under the `/rest` base URL stored in `TWENTY_BASE_URL` - strip the `/rest` suffix to derive it (e.g. `https://<host>/graphql`), and authenticate with the same `Authorization: Bearer <TWENTY_API_KEY>` header. It supports filtered data queries, e.g. `{ messages(filter: {subject: {ilike: "%invoice%"}}, first: 20) { edges { node { id subject } } } }`, per-object introspection via `{ __type(name: "Message") { fields { name } } }`, and a full type-name scan via `{ __schema { types { name } } }` - the reliable cross-check for whether an object is queryable when it is missing from REST metadata. GraphQL also exposes relation targets and query capabilities (filtering, aggregation) that REST metadata lacks. If the inspection reveals gaps, suggest a follow-up GraphQL introspection.
- **Write operations**: The script is strictly read-only.
