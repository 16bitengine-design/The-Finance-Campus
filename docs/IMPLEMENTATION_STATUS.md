# Implementation status and release boundaries

Last reviewed: 2026-11-22

This document distinguishes code that exists from integrations that have been exercised successfully. A workflow file, configuration flag or successful unit test is not proof that a live external integration works.

## Consolidated GitHub Actions layout

The repository now has four main workflows:

| Workflow | Responsibility | Triggers / modes |
|---|---|---|
| `.github/workflows/daily-topic-replenishment.yml` | Topic research/replenishment and script-candidate generation | Daily topic refresh at 08:30 EAT; manual `refresh_topics` or `generate_scripts` |
| `.github/workflows/production-validation.yml` | Real Kokoro end-to-end test and progressive Remotion sample | Manual `kokoro` or `progressive_sample`; progressive sample also runs when its source files change |
| `.github/workflows/quality.yml` | Unit tests, lint, renderer and Remotion quality checks | Push and pull request to main |
| `.github/workflows/buffer-operations.yml` | Public media hosting, Buffer discovery, dry-run, scheduling and publication monitoring | Manual `host_media`, `discover`, `dry_run`, `schedule`, `monitor`; monitor also runs every 30 minutes when enabled |

The workflows share responsibilities without merging unrelated Python modules into oversized files. Topic refresh never starts video production. Publishing modes remain separately gated.

## Implemented in the repository

| Capability | Current status | Important limitation |
|---|---|---|
| Brand, disclaimer and operating configuration | Implemented | Configuration validation does not replace editorial review. |
| Topic catalogue and duplicate protection | Implemented | Topic candidates still require claim-level review. |
| Daily topic refresh | Workflow implemented | A configured schedule is not proof every refresh run succeeds or reaches its target. |
| Script-candidate generation | Implemented, deterministic | It is not an LLM and does not perform semantic fact-checking. |
| Storyboard and whiteboard rendering | Implemented | Visual quality and narrative-to-illustration relevance still require human review. |
| Kokoro TTS integration | Implemented in code | The real-model CPU test must pass and its output must be reviewed before the narration pipeline is considered production-validated. |
| MP4 technical QC and captions | Implemented | Technical checks cannot establish whether visuals are educationally effective. |
| Automated quality workflow | Configured | The latest Actions run must be checked for a verified pass; workflow presence alone is not evidence. |
| Buffer publisher and duplicate-prevention ledger | Implemented in code | A real connected Buffer account and end-to-end tests are still required. |
| GitHub Releases media hosting | Guarded workflow implemented | Requires a production artifact, public repository and explicit human visual approval; not yet proven end to end. |
| Buffer publication monitor | Implemented in code and workflow | It remains gated by `BUFFER_MONITOR_ENABLED=true`; live Buffer read access and public URL verification must be tested. |
| Individual thumbnail download links | Implemented in monitor workflow | Links are exposed only after a post is publicly verified and a valid public release thumbnail URL is present. |

## Not yet production-operational

- Claim-by-claim financial fact-checking that proves each script claim is supported by a cited passage.
- Fully semantic visual QC that confirms illustrations accurately explain narration and that the video meets the desired aesthetic standard.
- Fully unattended daily video production with reliable topic selection, recovery and resource controls.
- A verified live Buffer scheduling and public publishing run.
- A complete end-to-end thumbnail hosting and download demonstration.
- Reliable operational notifications for failures and recovery actions.

## Release controls

- Do not enable live publishing until the visual standard is approved and the full production, hosting, scheduling and public-verification path has passed.
- Keep `BUFFER_PUBLISH_ENABLED` unset or false until explicitly approved.
- Keep the repository Actions variable `BUFFER_MONITOR_ENABLED` disabled until Buffer credentials are configured and monitor behavior is tested.
- Public media hosting requires an explicit `approve_public_hosting` selection after human visual review.
- A Buffer `sent` state alone is not proof of publication; only an approved destination URL that passes anonymous public retrieval is recorded as verified.
- Human visual review remains mandatory until semantic visual quality controls are demonstrated to be reliable.
- No paid service or paid API may be introduced without explicit approval.
- Kokoro remains the only approved narration engine.
- Topic refresh and script-candidate generation must not trigger rendering or publishing.

## Next engineering sequence

1. Validate the four consolidated workflows with GitHub Actions and resolve any workflow or test failures.
2. Complete and review the real Kokoro CPU end-to-end test.
3. Improve storyboard semantics, character interactions and the original illustration library.
4. Add explicit claim-review evidence and stronger source-support checks.
5. Run Buffer discovery and dry-run only after the account secrets are configured.
6. Test public media hosting and individual thumbnail links using an approved, reviewed sample.
7. Verify live scheduling and public destination checks before considering unattended publishing.

A capability is promoted from implemented to production-operational only after the relevant real integration has been exercised successfully and evidence is retained.
