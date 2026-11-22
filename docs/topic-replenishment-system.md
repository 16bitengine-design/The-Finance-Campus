# The Finance Campus — Topic Replenishment System

## Operating schedule

- GitHub Actions runs daily at 05:30 UTC (08:30 East Africa Time).
- The daily target is 3 newly accepted topic records (21 per week).
- A manual run can override the daily target through the workflow input.
- The workflow writes only to `production/topic-library.json` and `production/reports/topic-refresh-report.json`.

## Research and acceptance gates

A candidate is added only when:

1. Its stable topic ID and normalized title are not already in the library.
2. Its configured research source is HTTPS on an approved publisher domain.
3. The source returns HTTP 200 and remains on the approved publisher domain after redirects.
4. The source returns extractable page text.
5. At least the configured minimum number of mapped topic keywords are present in that text.
6. The candidate has a complete editorial brief, category, audience, geographic relevance and lifecycle fields.

A reachable PDF without extracted text is rejected. A source reachability/keyword check is evidence of relevance, not proof that every claim in a future script is supported. New records therefore remain `source_checked_needs_claim_review`; claim-level review is still required before production.

## Duplicate protection

- Stable IDs are derived from each curated blueprint slug.
- IDs and normalized titles are checked against the complete canonical library.
- The workflow validates that the final library has no duplicate IDs or exact normalized titles before committing.

## Safety boundaries

- Topic refresh does not create scripts, render videos, upload videos or publish anything.
- Script-candidate generation is manual-only and reads the same canonical topic library.
- YouTube and TikTok publishing remain disabled until the production pipeline is separately approved.
- Partial refreshes are retained only when they pass the source and duplicate checks. The workflow warns when fewer than 20 are available rather than inventing topics to hit the target.

## Reserve monitoring

Every refresh report records the catalogue size, number of unused blueprints, estimated weeks of cover at 21 topics per week, rejected candidates and any catalogue-exhaustion warning. The current curated blueprint catalogue is finite; at 3 topics per day, the 66-topic seed catalogue represents only about 22 days of supply. The warning is intentional. Daily replenishment increases freshness but does not itself create an unlimited supply. The next development step is broader, ongoing discovery from authoritative financial education resources, with extracted evidence and duplicate screening. The system must never fabricate an endless supply or silently recycle old topics.

## Editorial voice

Research sources supply evidence and factual grounding only. Topic titles, editorial briefs, examples and eventual scripts must use The Finance Campus' own distinctive voice—not copy the source's tone, phrasing or presentation. Explain ideas in clear, relatable language with engaging storytelling and realistic, hopeful framing.

## Canonical files

- Topic library: `production/topic-library.json`
- Daily workflow: `.github/workflows/daily-topic-replenishment.yml`
- Source and duplicate logic: `src/finance_campus/research_pipeline.py`
- Curated evergreen blueprint catalogue: `src/finance_campus/mindset_topics.py`
- Tests: `tests/test_topics.py`, `tests/test_research_pipeline.py`
