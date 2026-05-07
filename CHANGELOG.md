# Changelog

All notable changes to DevCD will be documented in this file.

The project follows Conventional Commits and Semantic Versioning once public releases begin.

## [0.1.1](https://github.com/mick-gsk/DevCD/compare/v0.1.0...v0.1.1) (2026-05-07)


### Features

* add ambient context kernel ([07c3ff1](https://github.com/mick-gsk/DevCD/commit/07c3ff10f3bd4a0598392a71f214c0e4c17a94c3))
* add daemon mascot to all brand assets and docs ([90a7fa6](https://github.com/mick-gsk/DevCD/commit/90a7fa6448a860c0d102693513be5ceb35e5857f))
* **agentic_context:** add local scout runner slice (ADR-011) ([a87cf75](https://github.com/mick-gsk/DevCD/commit/a87cf75e7fec9461d171cdcf13ee9da9efb3eaa3))
* **agentic_context:** add turn-0 startup signals and outcome eval telemetry ([2261ea7](https://github.com/mick-gsk/DevCD/commit/2261ea7bc6eed788e173b8ade52347cf649e43d0))
* **agentic_context:** add vision service integration to action packet ([bc9699c](https://github.com/mick-gsk/DevCD/commit/bc9699c38400d8a529081c65344cd9ad17db9d57))
* **agentic_context:** enrich action packet continuity contract ([e4e0904](https://github.com/mick-gsk/DevCD/commit/e4e0904dd84912041761ec986b989eb589841b79))
* **agentic_context:** enrich ActionPacket with blockers/withheld-context and add daemonless action-packet-demo CLI command ([ff45980](https://github.com/mick-gsk/DevCD/commit/ff459806579e28e823d65d249649501887df2c69))
* **agentic_context:** warm-start next action from priority queue ([c69a569](https://github.com/mick-gsk/DevCD/commit/c69a569d7d68adc77bc3a7070abf81956328d4a9))
* **agentic:** add metadata-first packs and vision intent delivery ([e00d58b](https://github.com/mick-gsk/DevCD/commit/e00d58bbd0b852810b2e5205c5c8d0d59c196f43))
* **ambient_context:** add agent layer workspace inspector and onboard integration ([24450f1](https://github.com/mick-gsk/DevCD/commit/24450f1840ab28533f4da14ccb152bda9700d3ec))
* **ambient_context:** add Context Packs and ContinuityPacket support ([0bc44b9](https://github.com/mick-gsk/DevCD/commit/0bc44b98fa2c4a8dbb17f000b3d6dc2f94186847))
* **ambient_context:** add context quality scoring and control-plane report ([495e375](https://github.com/mick-gsk/DevCD/commit/495e3757b060b8864ab7a54136dbbab4e51b3240))
* **ambient_context:** add context surfaces, agent resurrection, and handoff packet ([c7f535b](https://github.com/mick-gsk/DevCD/commit/c7f535bf0de7b876fb3fba630f9f1a641ee627b7))
* **ambient_context:** add ContextFeedback and ContextQualityReport models and service methods ([cd0ad74](https://github.com/mick-gsk/DevCD/commit/cd0ad74769ed19fa1515c0a7737fc6d8eebe201b))
* **ambient_context:** add curated warm-start continuity ([94c456d](https://github.com/mick-gsk/DevCD/commit/94c456d3c80e4f843315c50ff3708a920e06156a))
* **ambient_context:** add TUI surface with Textual ([cf8a854](https://github.com/mick-gsk/DevCD/commit/cf8a8540dc8405923b4a61fdb32203fba1172ce1))
* **ambient_context:** extend continuity packet with vision support ([f8fd4bc](https://github.com/mick-gsk/DevCD/commit/f8fd4bc76bcaeb4a4330e167ac212851c20a8c6d))
* **ambient_context:** extend surface models, brief generator, and add mcp_server slice ([1d67ba0](https://github.com/mick-gsk/DevCD/commit/1d67ba010fdfce507b59282e9658243266777b65))
* **ambient_context:** merge live git context and filter low-signal continuity hints ([1ca041a](https://github.com/mick-gsk/DevCD/commit/1ca041a4365a5454ab0ba13e9da8b59c425994f4))
* **ambient_context:** prioritize continuity and concise MCP context ([e0d5d1f](https://github.com/mick-gsk/DevCD/commit/e0d5d1ffd0c142e27ba96c597e7fbf2976e27eda))
* **ambient-context:** add two-stage continuity rotation thresholds ([b2df81e](https://github.com/mick-gsk/DevCD/commit/b2df81eedfe6cd8c8fd65d9ba3c321c005e41894))
* **ambient-context:** treat *_passed actions as successful outcomes ([0e78e99](https://github.com/mick-gsk/DevCD/commit/0e78e99e4ecf6a969fca1f91a0964380ec5c34b4))
* **brand:** add Continuity OS brand assets, design tokens, MkDocs wiring, and brand-system usage guide ([9de27ee](https://github.com/mick-gsk/DevCD/commit/9de27eeae4bab88d0ffb0f502c62b91cabef2d1d))
* **cli:** add context feedback and context quality commands ([b6ee20f](https://github.com/mick-gsk/DevCD/commit/b6ee20f989eb700dc1bc342d01b24dac266b73e3))
* **cli:** add context passport, context control, and integrations commands ([3f9fdc9](https://github.com/mick-gsk/DevCD/commit/3f9fdc923ae58549c460dd1d77121f548497839a))
* **cli:** add onboard command (agent-ready wrapper), update CHANGELOG ([d8b2991](https://github.com/mick-gsk/DevCD/commit/d8b29910d9119980cd479ea65f0329c090dd1d48))
* **cli:** add policy explain and simulate commands with Rich output ([8612069](https://github.com/mick-gsk/DevCD/commit/86120698bf620a6fb730246c4054ea5acc79e03f))
* **cli:** Add recipe git-commit command for post-commit hook integration ([d1eb203](https://github.com/mick-gsk/DevCD/commit/d1eb2035c1b6be649ffc3e33f8d940dfa6ead568))
* **cli:** add setup --yes flow and continuity skill scaffolding ([4295103](https://github.com/mick-gsk/DevCD/commit/429510387a31766d1205660b41db5ffa9bd0e8ef))
* **cli:** add setup wizard and ledger integrity check ([c1ae2cc](https://github.com/mick-gsk/DevCD/commit/c1ae2cc3bdc2d93b1068acd3e2338464e6923876))
* **cli:** add status, doctor, and context handoff-demo commands ([9e493b2](https://github.com/mick-gsk/DevCD/commit/9e493b27302db279cbd763edc2a8b75dbed76dbe))
* **cli:** add vision app with init/update/show/history commands ([afa52e0](https://github.com/mick-gsk/DevCD/commit/afa52e0ed0b0a8c4cc185d01eca9bb8fc6ade2e2))
* **cli:** add workflow commands and hook capture events ([a30d4ef](https://github.com/mick-gsk/DevCD/commit/a30d4effb51f6703082bdaa34f88208fd8e8c067))
* **cli:** add workflow, preset, and recipe scaffolds ([e6bd1e7](https://github.com/mick-gsk/DevCD/commit/e6bd1e7b23b0a4175df9d990ebf94e579ef1a299))
* **cli:** agent-ready init, zero-effort capture, quickstart, agentic commands ([b66e1dd](https://github.com/mick-gsk/DevCD/commit/b66e1ddfc640da69fa1ec3dcef25c9f3d9608c75))
* **cli:** enforce agentic completion gate and compliance metrics ([ce836e6](https://github.com/mick-gsk/DevCD/commit/ce836e629d1dcc2ea1000327cca94d67132fd176))
* **cli:** polish first-run terminal flows ([ae0f7df](https://github.com/mick-gsk/DevCD/commit/ae0f7df2665a0347b05d13241a8920fa11c8aba9))
* **cli:** setup-first quickstart und completion-guidance ([6fd639f](https://github.com/mick-gsk/DevCD/commit/6fd639f7d15fbf291583932cf1ba3a67a893bef4))
* **cli:** streamline onboard flow and add doctor fix ([8696177](https://github.com/mick-gsk/DevCD/commit/869617701fefba9f678ddf98cb974586cdd02d1c))
* **container:** add Docker sandbox image, .dockerignore, and CI container-build workflow ([d2e3bb0](https://github.com/mick-gsk/DevCD/commit/d2e3bb096ccf5f8dce23e1df35173a8e7b5c63ea))
* **dev:** add fast local check targets ([272e9c6](https://github.com/mick-gsk/DevCD/commit/272e9c680ecacbcaed1cc712c1944bcbc138f38e))
* devcd welcome command with zero-write onboarding path ([2c968af](https://github.com/mick-gsk/DevCD/commit/2c968af8aa526e5347fbefacd90cc6703bad3978))
* **events:** Add git-commit recipe for capturing commits as DevCD events ([a3ff645](https://github.com/mick-gsk/DevCD/commit/a3ff645b7e19beb327303806f78f0019f7d3c722))
* **events:** add PytestFailure event recipe and re-export from slice __init__ ([4cde088](https://github.com/mick-gsk/DevCD/commit/4cde088a76d90d6e3ba27d6138900e10a861e498))
* **events:** add research-session recipe with policy-gated source and note events ([c799520](https://github.com/mick-gsk/DevCD/commit/c7995201bc31d88b09df0b161023ad5431084845))
* **events:** support subtask completion records in ledger ([922e55a](https://github.com/mick-gsk/DevCD/commit/922e55a85fde756496a39865f7b386b85de397e4))
* **host_state_engine:** record withheld signals with safe metadata in state ([618e288](https://github.com/mick-gsk/DevCD/commit/618e288932efa7763b1eb5aa138ddeae17ee9cd2))
* implement US1-US5 core DevCD context daemon features ([915b897](https://github.com/mick-gsk/DevCD/commit/915b897402bcec67feefc14fb7ff0b86a568791e))
* **mcp_server:** expose agent-handoff-packet as MCP resource ([6ce5d1e](https://github.com/mick-gsk/DevCD/commit/6ce5d1ec7a3c77478eb0f1716b075dc85cd0b499))
* **mcp_server:** extend MCP server resources for new context surfaces ([071d065](https://github.com/mick-gsk/DevCD/commit/071d0659d26c7d2dc5ac87ab730a12670416347b))
* **mcp:** add concise and detailed context resource URIs ([0e84c3e](https://github.com/mick-gsk/DevCD/commit/0e84c3e3fea956dc19152ac1676af45a9dd5fc12))
* **policy_layer:** add agentic runner policy gate ([62ede9f](https://github.com/mick-gsk/DevCD/commit/62ede9faba6ad9f2f5ceed0b57e5aecf56a3bd74))
* **policy_layer:** add PolicyDecisionExplanation, PolicySimulationReport, explain_decision and simulate_event ([704501a](https://github.com/mick-gsk/DevCD/commit/704501ab73495bf5e7e6ffa15e0dab9755e5b155))
* **policy_layer:** add vision injection policy decision ([ebe2644](https://github.com/mick-gsk/DevCD/commit/ebe2644e43b808f2523555d7b720ed67cbb9b6be))
* **services:** Update ambient context and state engine for event integration ([d81b729](https://github.com/mick-gsk/DevCD/commit/d81b729da408264a93d1d067f5d1a2e281b3aebc))
* **skills:** add devcd-continuity agent skill for OpenClaw and continuity workflows ([e81ebe3](https://github.com/mick-gsk/DevCD/commit/e81ebe34e33da67f4dfc19314dce8f3f215886ed))
* **state-engine:** enrich handoff attempt summaries ([b1e7554](https://github.com/mick-gsk/DevCD/commit/b1e75545e32501a0f26ff0d5cc213766d8102a8f))
* **vision_layer:** implement vision layer slice with models, service, and tests ([84435b2](https://github.com/mick-gsk/DevCD/commit/84435b2bfd6a661c966c2b924116147e30e4b534))
* **workflow:** add workflow slice and API integration ([91c525a](https://github.com/mick-gsk/DevCD/commit/91c525ad9a1f13c53c0af40fb48ab7225e2e766d))


### Bug Fixes

* align test_failure event type in state engine and test ([ad01e5f](https://github.com/mick-gsk/DevCD/commit/ad01e5fbecedb64386a98fe7b213e71eaff5edc4))
* apply ruff format to resolve CI format check failures [self-heal] ([#37](https://github.com/mick-gsk/DevCD/issues/37)) ([e87ba24](https://github.com/mick-gsk/DevCD/commit/e87ba24142ace2cac739bc4678243262ffd80840))
* apply ruff formatting to resolve CI format check failures ([#20](https://github.com/mick-gsk/DevCD/issues/20)) ([3130e9b](https://github.com/mick-gsk/DevCD/commit/3130e9b29fdc843b5ba8f36a06898779b342f35a))
* **core:** harden state dedup, fulltext deny, and env catalog warning ([078fe73](https://github.com/mick-gsk/DevCD/commit/078fe73fa45f5ffbffd5aae583a4cd992c1739cc))
* handle Rich ANSI codes in capture rejection test assertions [self-heal] ([#23](https://github.com/mick-gsk/DevCD/issues/23)) ([dd199b9](https://github.com/mick-gsk/DevCD/commit/dd199b910c1b370e473bcb4dad2338c12ca6a53f))
* move dependencies out of [project.urls] into [project] block ([bf815e6](https://github.com/mick-gsk/DevCD/commit/bf815e66ba816cbdf566c8550c48377edfd6c3aa))
* reformat 4 files to pass ruff format check [self-heal] ([#7](https://github.com/mick-gsk/DevCD/issues/7)) ([c355953](https://github.com/mick-gsk/DevCD/commit/c355953dadcb254c0c763cfb7708334d611ef2d1))
* reformat tests/test_cli.py to pass ruff format check [self-heal] ([#17](https://github.com/mick-gsk/DevCD/issues/17)) ([52f498e](https://github.com/mick-gsk/DevCD/commit/52f498edf8bfaa22e690ade936ee202f10354aeb))
* stabilize CI help tests [self-heal] ([cc536e5](https://github.com/mick-gsk/DevCD/commit/cc536e56cb4ddd12cae3361302666c8d29317191))
* strip ANSI codes before asserting CLI help option names [self-heal] ([#5](https://github.com/mick-gsk/DevCD/issues/5)) ([b8bca55](https://github.com/mick-gsk/DevCD/commit/b8bca550af24e1a25aee204b228f8f3e7a760bb5))
* use copilot token for self-heal ([10324cf](https://github.com/mick-gsk/DevCD/commit/10324cf9f895b486b134632cf8832e1d3a3754a9))


### Documentation

* add ADR-006, ADR-007, agent superpowers docs and continuity examples ([28b7a87](https://github.com/mick-gsk/DevCD/commit/28b7a8750e324a24ebb05372aeca118f4b07c3a4))
* add ADR-012, publishing/release-readiness/openclaw/container/context-packs guides, and context-pack examples ([8fea514](https://github.com/mick-gsk/DevCD/commit/8fea51425850d1624299acfd4865db2ff7fe6c9b))
* add agent landscape, update agent-consumption + ADR-011, nav and session plans ([9532540](https://github.com/mick-gsk/DevCD/commit/9532540039b97904270e9a5c1ffcae2f48c6c304))
* add agent-consumption guide, update README, docs, examples, and llms.txt ([017702c](https://github.com/mick-gsk/DevCD/commit/017702c77cbc79c1e96300cf1b1fbafb54295f9f))
* add MkDocs Material + GitHub Pages deploy workflow ([a1a4230](https://github.com/mick-gsk/DevCD/commit/a1a42309c417090557207708376f2033f17a6a9a))
* add OpenClaw MCP integration spike and use-case draft ([3e7fd47](https://github.com/mick-gsk/DevCD/commit/3e7fd4748f9114fa669eb1669a62f7e271d76b2d))
* add PyPI release runbook ([e5127bd](https://github.com/mick-gsk/DevCD/commit/e5127bd30c906154b0f46d23f44892b0359adb45))
* add research-continuity example with continuity packet output ([1b9b2ee](https://github.com/mick-gsk/DevCD/commit/1b9b2eec1d027568585ca7e17285670a69221821))
* **adr:** add ADR-019 workflow orchestration and trust layers ([4457453](https://github.com/mick-gsk/DevCD/commit/4457453b9ea4de9940ac5ab203722513ddfc0ce4))
* **adr:** record deferral of per-event-class ttl config ([4355ba8](https://github.com/mick-gsk/DevCD/commit/4355ba845ec2a8e444a459de43cacab55d622465))
* **agent-ops:** add continuity instructions for local agents ([381134a](https://github.com/mick-gsk/DevCD/commit/381134a4527411544951089021e469fa9364348f))
* **agentic_context:** document do-not-repeat rationale contract ([4cc7ba7](https://github.com/mick-gsk/DevCD/commit/4cc7ba7e765aaae425d97f44244126727f47c137))
* **agentic:** add complexity blueprint and live run harness ([b315f93](https://github.com/mick-gsk/DevCD/commit/b315f93610bd4f207880a4b900dc5c7cef109833))
* **branding:** add cache-busted mark and avatar to docs pages ([ea4bc3d](https://github.com/mick-gsk/DevCD/commit/ea4bc3d06bc20eca9282a3550317275360af7a11))
* **continuity:** erweitere startup- und capture-leitlinien ([82ac6e7](https://github.com/mick-gsk/DevCD/commit/82ac6e70dfeff579ccc1f98a02b3aa759feb8760))
* **decisions:** add ADR-008 agent continuity layer and context packs ([9be3e10](https://github.com/mick-gsk/DevCD/commit/9be3e10ab1aa17a11b8587e8bb58464d388b0f93))
* **examples:** Add cross-agent-handoff example ([c4d397f](https://github.com/mick-gsk/DevCD/commit/c4d397fb52761485b5a2fbddf469759c13739b59))
* improve first-run positioning ([a8fd884](https://github.com/mick-gsk/DevCD/commit/a8fd884429ec9747bca859e17efbcf9d2196a7b9))
* **instructions:** reinforce public-product quality principle ([208f5cb](https://github.com/mick-gsk/DevCD/commit/208f5cb6ef7ee6fd204c8dceb5eb0a4f88f70d9a))
* **instructions:** streamline continuity guidance block ([0c88db6](https://github.com/mick-gsk/DevCD/commit/0c88db608db923ebd01a1e8b1250e37e6725ed8d))
* mark devcd 0.1.0 as published on PyPI ([0087c2c](https://github.com/mick-gsk/DevCD/commit/0087c2c580b1f491fe67a6d7fffc03d1e9c0b89f))
* **onboarding:** document skills-first flow and compliance checks ([27080c8](https://github.com/mick-gsk/DevCD/commit/27080c85f82e561aad641925ba6bca37ac7bcefa))
* **onboarding:** make onboard the primary first-run path ([11c4add](https://github.com/mick-gsk/DevCD/commit/11c4adde7b2e05ed7043b4ae3c7bfb0b8c490870))
* **onboarding:** switch first-run guidance to devcd setup ([8e22264](https://github.com/mick-gsk/DevCD/commit/8e2226409982fd256f475b844d3b361ebdb0acef))
* OpenClaw onboarding benchmark and getting-started guide ([93b03cd](https://github.com/mick-gsk/DevCD/commit/93b03cdfb6deb6b6492a245838121c25b3f8f423))
* **openclaw:** update integration guide, packaging spike, and use-case docs ([3271a5f](https://github.com/mick-gsk/DevCD/commit/3271a5f5b063b227851d579c6b60e2c14f772859))
* product-led README rewrite, expanded SECURITY policy, updated CONTRIBUTING and getting-started ([5ce78a8](https://github.com/mick-gsk/DevCD/commit/5ce78a8913651d645be791e9c768d7e2e94a19e5))
* restore single README wordmark ([5f468d7](https://github.com/mick-gsk/DevCD/commit/5f468d7a26309390773f977c00b6173cbcf11b21))
* **site:** add brand CSS, update homepage hero and site description ([ae0576f](https://github.com/mick-gsk/DevCD/commit/ae0576fbed9b140a145592e5faeb75eac3c0f42b))
* **site:** rebuild static docs output ([28d8770](https://github.com/mick-gsk/DevCD/commit/28d8770043505f62200317c42be1bb0eae4c18a1))
* **site:** redesign homepage hero and paths ([a587dee](https://github.com/mick-gsk/DevCD/commit/a587deeb42092bd13c4789eec0e7aff47db4f4e8))
* **site:** refresh generated documentation output ([3eeb225](https://github.com/mick-gsk/DevCD/commit/3eeb2252fef14b99341d54cc226afa8a86854dea))
* **site:** refresh generated documentation output ([99f53b8](https://github.com/mick-gsk/DevCD/commit/99f53b89546fb155f95cfe840616d743075496df))
* update context-brief schema, add ADR-002 through ADR-005, event-source-recipes doc and README ([2961496](https://github.com/mick-gsk/DevCD/commit/2961496ab71e9944c7e5173fc00d8db85fdb95a4))
* update docs, examples, llms.txt, and CHANGELOG for new features; add devcd.toml ([3faef9c](https://github.com/mick-gsk/DevCD/commit/3faef9c58aa5be1c948370683f83621081036ce4))
* Update README and CHANGELOG for welcome feature ([3273484](https://github.com/mick-gsk/DevCD/commit/32734840a527b06c72ea313ecbc67817fe8339b0))
* update README, getting-started, agent-consumption and llms.txt ([137241b](https://github.com/mick-gsk/DevCD/commit/137241be4fe6a516325aeeeb75316b03d8a8b904))
* update README, VISION, getting-started, and nav ([15ab625](https://github.com/mick-gsk/DevCD/commit/15ab625587a2bc62b9074a8a5b5bb7e84ec9d74c))
* update README, VISION, use-cases and agent-resurrection for continuity packs ([5040931](https://github.com/mick-gsk/DevCD/commit/5040931d94b2444439a5750bc679acd9f001ef25))
* update site branding and homepage ([696933a](https://github.com/mick-gsk/DevCD/commit/696933aa2ab7f70e8a7fc4682f02a432e76ded95))

## 0.2.1 - 2026-05-07

Short version: Action Packet now projects verification-ready session contracts, rejected dead-end paths, and additive vision-alignment signals for completion/compliance. New workflow_layer slice adds resumable YAML workflow runner, trust-bounded catalog stack, and layered instruction resolver.

### Added

- New scaffold helpers: `devcd workflow new`, `devcd workflow list`, `devcd preset new`, `devcd recipe new`, and `devcd recipe run`, plus built-in starter workflows and custom recipe YAML loading under `.devcd/`.
- Continuity packets now rank high-signal references by kind and freshness, while concise MCP resources trim long lists and annotate the intended startup read order.
- New `workflow_layer` slice: resumable YAML workflow runner with human-gate pause/resume, `WorkflowEngine` persisting run state under `.devcd/workflows/runs/`, and `CommandStep`/`ShellStep`/`GateStep` step types.
- `WorkflowCatalog` with trust-bounded resolution stack (builtin → user → project → env); env-supplied URLs validated for HTTPS/localhost; `CatalogTrustError` on invalid sources.
- `InstructionLayerResolver` composing agent instruction content from managed-core, team-preset (`.devcd/presets/<target>-*.md`), and workspace-override (`.devcd/instructions/<target>.md`) layers with replace/wrap strategies.
- `_write_agent_instruction` now routes through `InstructionLayerResolver` so workspace overrides and team presets are automatically composed on top of the managed DevCD block.
- New `devcd workflow` CLI sub-group with `run`, `status`, `resume`, and `info` commands.
- Workflow command steps now support in-process CLI execution via an injected command runner, reducing reliance on external `devcd` subprocess lookup.
- New read-only HTTP API surface for workflow catalog discovery and resolution: `GET /workflow/catalog` and `GET /workflow/catalog/{name}`.
- Continuity hook capture points added around key orchestration commands: before/after `setup`, before/after `agentic action-packet`, and before/after `handoff`.
- Three new `PolicyEngine` decision methods: `decide_workflow_step_execute`, `decide_catalog_install`, `decide_instruction_layer_write`.
- ADR-019: architecture decision record for workflow orchestration, catalog trust stack, and layered instruction resolver.
- Action Packet additive fields: `rejected_paths` and a dedicated `session_contract` shape (`next_action`, `done_when`, `verification_required`, `withheld_count`).
- Local CLI and MCP Action Packet builders now inject configured workspace vision consistently, and `devcd agentic completion-check` / `devcd agentic compliance` add a policy-safe vision alignment note with warnings on clear drift.
- Action Packet projection now derives `done_when` from `event_class="goal.done_when"` and sets verification requirements when completion criteria are missing.
- Read-only MCP `devcd://context/session-contract` now exposes the Action Packet session contract contract with matching context budget metadata.
- New `event_class` support on `DevEvent` with validated `dead_end` and `goal.done_when` payload contracts.
- `dead_end` continuity curation support for developer-triggered non-retriable approach tracking (`approach_summary`, `reason`, `related_goal`).

## 0.2.0 - 2026-05-06

Short version: Initial local-first context daemon foundation with context quality scoring, control-plane report, research-session recipe, live Agent Passport, MCP integration snippets, and daemonless Action Packet demo.

### Added

- Faster local development gate: `make check-dev` now uses `dmypy` and affected-test execution via `pytest-testmon` (with automatic fallback), plus `make test-fast-parallel` for optional `pytest-xdist` parallel runs.
- New `devcd setup` install-time wizard for interactive multi-project configuration, manual agent-target selection, and automatic initial handoff seeding so `devcd agentic action-packet` is usable immediately after first setup.
- CLI polish for first-run flows: root `devcd --version`/`-V`, `devcd smoke --compact`, and richer terminal rendering for `welcome`, `onboard`, and `doctor`.
- `devcd welcome` zero-write first-run guide, Smoke next-step output, and OpenClaw product benchmark notes to make installation and onboarding feel more guided and product-grade.
- `devcd doctor --fix` policy-gated local repair mode with explicit receipts for applied or denied config/profile scaffolding actions.
- Agent-Layer onboarding for `devcd onboard --preview` and `devcd onboard --yes`, including metadata-only workspace detection, persisted `.devcd/agent-layer-profile.json`, Quickstart Agent Layer console, read-only workspace/profile inspectors, and Smoke/Doctor readiness checks.
- Public-consumption docs for release readiness and publishing now distinguish the future PyPI path from checkout installs and point first-time evaluators at a curated examples index plus `devcd smoke` as the install check.
- Context budget and session contract surfaces for Agent Passports, Action Packets, `devcd context budget`, and the read-only `devcd://context/session-contract` MCP resource.
- `ActionPacketBlocker` and `ActionPacketWithheldContext` models on `ActionPacket` for structured blocker and withheld-context surfaces.
- `devcd agentic action-packet-demo --events <file.jsonl>` daemonless CLI command that replays raw DevEvents into an in-memory service and renders the Action Packet contract via `--json` or human-readable markdown.
- `_render_action_packet` helper that renders the full Action Packet (start brief, evidence, blockers, do-not-repeat, withheld context, policy summary) as human-readable markdown.
- `devcd-continuity` agent skill under `skills/devcd-continuity/` for OpenClaw and agent-continuity workflows.
- Agent Landscape documentation (`docs/devcd/agent-landscape.md`) describing the DevCD-in-the-wild ecosystem.

- Research-session event recipe (`devcd recipe research-session`) with policy-gated source, note, and full-text events.
- Context quality scoring: deterministic local score, category counts, risk notes, and suggested next actions on `ContextQualityReport`.
- Context control-plane report model (`ContextControlReport`) with visible/withheld sources, memory counts, continuity preview, and quality summary.
- `GET /context/control-plane` API endpoint exposing the control-plane report.
- `devcd context passport` CLI command to generate a live policy-filtered Agent Passport from the local ledger.
- `devcd context control` CLI command to display the control-plane report (`--json` supported).
- `devcd onboard` first-run wrapper that creates local config, prepares selected agent instruction files, and prints the Agent Passport path without starting a daemon or mutating external config.
- `devcd integrations openclaw` and `devcd integrations hermes` CLI commands with copyable local MCP config snippets and optional `--smoke-test` shape check.
- Release readiness documentation and `make distribution` verification for wheel metadata, typed package marker, and installed CLI smoke tests.
- Container sandbox Dockerfile with CI build and CLI smoke-test workflow.
- Context Packs documentation and examples describing DevCD's metadata-only extension surface.
- Manual PyPI Trusted Publishing workflow and publishing guide for verified release artifacts.
- Context Pack and Event Recipe issue templates plus slice labeler updates for current package layout.
- `make smoke` target for a daemonless local CLI sanity check.
- OpenClaw integration guide that separates verified local MCP behavior from unclaimed gateway E2E status.
- Product-led README rewrite with OpenClaw-style first screen, status table, quickstart, trust defaults, and docs-by-goal navigation.
- DevCD Continuity OS brand system with mark, wordmark, viral social-card/avatar artwork, design tokens, README/MkDocs wiring, and usage guidance.
- Default `devcd.toml` configuration file committed to the repository root.
- Python monorepo scaffold with Vertical Slice Architecture.
- MVP daemon API for `POST /event`, `GET /state`, and `GET /memory/{scope}`.
- Default observe-only policy layer with explicit policy reasoning.
- Working-memory store with 5-minute TTL.
- Local JSON Lines event ledger.
- Initial state and event JSON Schemas.
- Runtime config via `devcd.toml` and `DEVCD_` environment variables.
- CLI commands for config initialization and event submission.
- Git snapshot source for branch and latest-commit events.
- Context feedback and context quality report models and CLI commands.
- Context surfaces (coding-agent, review-agent, debugging-agent, subagent, public-demo) with surface-aware brief generation.
- Agent resurrection and handoff packet models (`AgentResurrectionContext`, `AgentHandoffPacket`).
- `devcd context handoff-demo` command for machine-readable agent-continuity hand-off output.
- `devcd status` and `devcd doctor` operational readiness CLI commands.
- MCP resource `devcd://context/agent-handoff-packet` exposing the agent-continuity packet.
- JSON Schema for the agent handoff packet (`schemas/devcd-agent-handoff-packet.schema.json`).
