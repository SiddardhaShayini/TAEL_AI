# TAEL V3: Task-Adaptive Efficient Language AI

## 1. Product Vision

**TAEL V3** is a local-first AI software creation and research assistant for everyday laptops. It turns natural-language requirements into working, tested software; helps investigate technical questions using the live internet; and can operate approved desktop tools when the user explicitly permits it.

V3 builds on the useful foundations in TAEL V2—local Granite inference, task routing, a VS Code interface, workspace tools, project memory, and an 8GB laptop target—while addressing the gaps identified in the V2 project: a narrow tool set, no integrated web research or general desktop-app workflow, brittle heuristic routing and tool-call parsing, limited cross-project context, incomplete resource controls, and benchmark results that do not consistently reflect the model's actual reliability.

V3 is an AI product with an agentic workflow, not an unrestricted autonomous process. It can plan and carry out multi-step work, but users remain in control of consequential actions, access to private data, and external side effects.

## 2. Name and Identity

- **Product name:** TAEL AI
- **Version title:** TAEL V3
- **Name expansion:** Task-Adaptive Efficient Language AI
- **Slogan:** "Capable local AI, built for everyday hardware."
- **Primary users:** Developers, students, researchers, and makers using CPU-only laptops, especially systems with 8GB RAM.
- **Primary platform:** Windows desktop, with a design that can support Linux and macOS where the required integrations exist.

## 3. V3 Goals

1. **Natural-language software creation:** Plan, create, modify, debug, test, document, and explain complete software projects through conversation.
2. **Hardware-aware engineering:** Understand target hardware and deployment constraints, and recommend or implement resource-conscious designs.
3. **Autonomous optimization with review:** Profile software, find bottlenecks, propose improvements, and verify measurable changes without silently making risky system changes.
4. **Deep internet research:** Search multiple sources, open and inspect pages, follow references where useful, reconcile conflicting information, and provide traceable citations and uncertainty.
5. **Permissioned desktop assistance:** Open approved applications such as a browser, editor, terminal, Notepad, or Word, and use supported UI automation only within the user's approved scope.
6. **Extensible tools:** Support a curated tool registry and compatible integrations (including MCP where practical), instead of limiting capabilities to V2's fixed set of ten workspace tools.
7. **Reliable, resource-aware operation:** Remain usable on 8GB RAM CPU-only laptops by measuring actual resource use and adapting work before the system becomes unstable.
8. **Privacy and user control:** Keep model inference local by default, disclose when a task needs the internet, and ask before accessing sensitive data or causing significant external or irreversible effects.
9. **Easy for anyone to start:** Make installation, first-run setup, and everyday use simple enough for non-experts, with a single downloadable installer/package or a single setup-and-launch command.

## 4. V2 Baseline and Lessons

TAEL V2 already provides a quantized IBM Granite 3.1 2B model, Ollama and `llama.cpp` paths, a Python agent loop, a keyword-based task router, XML-style tool-call parsing, workspace-scoped file and Git tools, bounded Python/terminal execution, JSON-backed conversation/project/file/summary memory, and a VS Code extension with streaming, diff preview, diagnostics, and tool execution. It also includes training-data builders, deployment scripts, evaluation reports, and tests for several subsystems.

V3 should preserve these strengths where they remain useful, but improve the following:

- **Model capacity and verification:** V2's own capability report records partial results in combinatorics and Git and qualitative-only results in several other areas, despite broader 100% benchmark claims elsewhere. V3 must report results by task, use reproducible tests, and distinguish measured performance from claims.
- **Tool coverage:** V2's registered tools focus on workspace files, Git, Python, and terminal commands. V3 needs separately permissioned web search/retrieval, research, app launch, and supported desktop integrations.
- **Safety model:** A workspace path boundary and command-pattern blacklist are not a complete isolation or consent system. V3 needs explicit capability grants, approval gates, process isolation where available, auditable actions, and safe defaults.
- **Routing and tool use:** V2 relies on keyword scoring and a tolerant custom XML protocol. V3 should use structured tool schemas, validated arguments, explicit tool results, bounded retries, and transparent fallback when the model is unsure.
- **Context and memory:** V2 uses estimated token counts, a 4,096-token budget, BM25-like keyword retrieval, and local JSON files. V3 needs measured model context limits, better project indexing and retrieval, configurable retention, and a clear way to inspect, export, and delete memory.
- **Resource management:** V2 describes a small model footprint but does not provide a complete runtime-wide resource governor. V3 must account for the model, KV cache, Aider, indexing, browser/tool subprocesses, and other running applications together.
- **Scope and UX:** V2 has useful VS Code affordances but does not provide a cohesive workflow for research, multi-application tasks, approval, cancellation, recovery, and final verification.

These are planning priorities, not claims that V3 has been implemented.

## 5. Core User Experience

### 5.1 Software creation workflow

For a request such as "Create a small inventory app with offline storage and tests," TAEL should:

1. Clarify material ambiguities and state its proposed scope.
2. Inspect the selected workspace and identify its language, framework, existing conventions, and relevant files.
3. Produce a short, editable task plan for multi-step work.
4. Use Aider to make focused, reviewable changes with IBM Granite Code 3B providing local code-generation and reasoning.
5. Run the appropriate tests, linters, builds, and safe diagnostics; inspect failures and iterate within configured limits.
6. Show changed files, verification results, known gaps, and a concise completion summary.

The user can review a diff, stop the run, reject an action, or revert changes through version control. TAEL must not claim tests passed unless it actually ran them and observed success.

### 5.2 Research workflow

For a research request, TAEL should clarify freshness or source-quality requirements if they affect the answer, search more than one relevant source when warranted, read source pages rather than relying only on snippets, compare evidence, and return a synthesized response with links, dates where available, and uncertainty or disagreement made explicit. Retrieved web content is untrusted data, not instructions to execute tools or disclose private information.

### 5.3 Desktop-app workflow

TAEL may offer to open an application or URL through an approved integration. Before launch or UI interaction, show the application/action and obtain the required permission. App control must be limited to supported integrations and the granted scope; arbitrary keystrokes, clicks, or background control are never implied by a general request to use a tool.

### 5.4 Beginner-friendly onboarding

- Provide a clear welcome flow that checks the laptop, explains local model setup and storage needs, and recommends a suitable resource profile without requiring users to understand model runtimes or command-line configuration.
- Keep the everyday interface approachable: plain-language controls, sensible defaults, guided examples, visible progress, clear errors with recovery steps, and no need to know agent/tool terminology.
- Make advanced settings available when wanted, but do not require manual editing of configuration files for a normal installation or first task.
- Explain when internet access is needed to obtain the model or perform research, show download sizes and destinations, and allow the user to cancel or resume downloads.

## 6. Proposed V3 Architecture

Keep the system modular so the 3B model is not expected to perform every job itself:

1. **User interfaces:** A lightweight desktop/CLI experience and the existing VS Code workflow, with a consistent chat, task plan, diff, approval, cancellation, resource-status, and history experience.
2. **Task orchestrator:** Converts a request into bounded steps, selects Aider, research, or desktop workflows, manages budgets and approvals, and reports progress. It must stop safely on cancellation, repeated tool errors, budget exhaustion, or missing permission. A single local orchestrator/API owns session state, routing, and model-engine lifecycle; clients must not start duplicate inference backends or maintain conflicting policy.
3. **Coding engine:** Aider is the primary coding/editing orchestrator. TAEL provides local model configuration, project context, permission-aware tool integrations, and a verification/review loop rather than duplicating Aider's core editing role.
4. **Local model runtime:** IBM Granite Code 3B, served by a supported local inference backend such as Ollama or `llama.cpp`, using a tested quantized model appropriate to the machine. Keep the selected backend and model artifact configurable without requiring cloud inference.
5. **Typed tool and connector layer:** A registry exposes narrowly scoped tools for workspace operations, tests, Git, web research, and approved desktop actions. Each tool declares its input schema, capability requirements, resource/time limits, and whether user approval is required. Tool registration and invocation must work across the service/client boundary with typed results; local client callbacks must not be assumed to exist in the service. Add integrations through documented adapters, including MCP-compatible servers where feasible.
6. **Context and memory:** A project-aware context provider combines active editor context, repository structure, diagnostics, relevant code/documentation, and the built-in persistent project-memory system. It retrieves a bounded, relevant subset rather than injecting a whole project history; memory stays local by default and has user-visible management controls. Keep transient session history distinct from durable project memory, and bound session archives and retention as well as active caches.
7. **Policy and approval service:** Enforces workspace boundaries, user grants, per-action confirmation, and audit records independently of model output. The model cannot grant itself permissions.
8. **Resource supervisor:** Samples available memory, process memory, CPU activity, inference queue, and tool subprocess usage; applies backpressure and resource profiles across all components.
9. **Evaluation and diagnostics:** Records opt-in local run metrics, tool outcomes, model/runtime settings, and reproducible task results without collecting private project content for telemetry.

### 6.1 Built-in persistent project memory for agents

TAEL V3 must include its own persistent project-memory feature for the projects users work on. It gives the agent reusable project knowledge between tasks, reducing repeated broad discovery and unnecessary context tokens. This is a product feature, not the repository's `PROJECT_MEMORY.md`: that repository file is development continuity for people and agents building TAEL itself, and must not be used as the runtime memory store for TAEL users' projects.

**Storage approach**

- Maintain a separate memory namespace for each user-selected project, keyed to a stable project identity and kept in TAEL's local application data by default so enabling memory does not silently add files to or modify the user's repository.
- Use a small local SQLite database as the runtime source of truth, with SQLite FTS5 full-text search for fast local retrieval. Store concise, inspectable entries with category, project identity, tags, creation/update time, verification status, source paths, and supersession links.
- Provide user-readable Markdown export/import for portability and inspection. Do not require agents to read a monolithic Markdown file on every task; do not use full conversation transcripts or source-file copies as memory.
- Keep the initial implementation local and lightweight. Start with FTS5 ranking plus metadata filters (project, category, recency, verification, and task relevance); consider embedding/semantic retrieval only if evaluation shows keyword retrieval misses important cases and measured resource cost is acceptable.

**Task retrieval and updates**

- At task start, give the agent only a short project profile and a bounded set of entries retrieved from the user's task and active project context. Enforce a configurable memory-token budget and expose which entries were supplied.
- Let the agent search memory on demand during a task, instead of loading all stored knowledge up front. Keep detailed history searchable for follow-up questions.
- Store concise facts, decisions, assumptions, conventions, recurring pitfalls, completed work, and open work. Mark assumptions and unverified claims as such; link claims to source paths or task outcomes where possible.
- After meaningful work, let the agent propose focused additions or updates. Detect duplicates and contradictions, update or supersede stale entries instead of endlessly appending, and preserve useful history. Do not store secrets or unnecessary user content.
- Treat memory as a hint, not proof: verify relevant remembered claims against current files, tests, and runtime state before acting on them. Surface stale or conflicting entries rather than silently treating them as current.
- Give users controls to inspect, search, edit, disable, export, import, and delete project memories, including clearing a single project. Keep namespaces isolated and memory local unless the user explicitly chooses otherwise.
- Apply existing privacy, permission, and untrusted-content rules to memory reads and writes. Memory content cannot grant permissions or override system, developer, or user instructions.

## 7. Model and Runtime Strategy

- **Primary model:** IBM Granite Code 3B, with the exact instruct/checkpoint variant, license, model card, prompt format, and tool-call compatibility verified before release.
- **Inference:** CPU-only local inference is the baseline. Prefer a supported 4-bit quantized model for constrained systems; compare quantization quality against the original model on the V3 evaluation suite before selecting a default.
- **Orchestration:** Use Aider for coding tasks and integrate it with the chosen local Granite endpoint. Validate the exact Aider version, model alias/provider configuration, and tool hand-off path during the initial feasibility phase.
- **No assumption of free capacity:** The 3B model is larger than V2's 2B model. Measure resident memory, KV-cache growth, context capacity, and tokens per second on representative 8GB machines; do not reuse V2's memory or speed claims.
- **Fallback behavior:** If the selected model, local runtime, or Aider integration is unavailable, report the cause and offer a clear, user-approved alternative. Never silently send source code or prompts to a cloud model.
- **Workload selection:** Use deterministic tools for exact calculations, file operations, tests, and system facts; use the model for planning, code, explanation, and synthesis. Prefer small, verifiable steps over long ungrounded generations.

## 8. Tooling, Permissions, and Safety

### 8.1 Permission levels

- **Read-only workspace access:** Granted for the selected project and visible in the current session.
- **Workspace changes:** Show a diff or clear file-level summary; preserve existing work and provide recovery through Git or backups where practical.
- **Command execution:** Explain the command, working directory, expected effects, timeout, and resource limit. Require confirmation for destructive, privileged, network-changing, or out-of-workspace commands.
- **Internet access:** Clearly indicate when a search or page fetch is about to occur. Send only the query and data needed for that request; do not upload workspace files or conversation history by default.
- **Application launch and UI automation:** Confirm the application, target, and permitted interaction before launch or control. Keep grants narrow, visible, revocable, and time-bounded.
- **External side effects:** Require explicit confirmation before sending messages, submitting forms, publishing content, purchasing, changing accounts/settings, pushing code, or modifying remote systems.

### 8.2 Safety requirements

- Enforce workspace confinement using canonical paths and account for symlinks, junctions, alternate path forms, and platform differences.
- Replace blacklist-only command protection with an allowlisted/sandboxed execution design where feasible. Use least privilege, restricted working directories, timeouts, output caps, cancellation, and process cleanup.
- Do not expose secrets to the model or connectors by default. Redact credentials in logs and block secret-file access unless a narrowly defined, user-approved operation requires it.
- Treat repository files, tool results, search snippets, and web pages as potentially adversarial input. Do not follow their embedded requests to reveal secrets, ignore policy, or take unrelated actions.
- Validate tool names, schemas, argument types, output size, and approval state before dispatch. Require confirmation again when an action exceeds its granted scope.
- Maintain an inspectable local activity log containing action, tool, scope, outcome, and approval—not unnecessary source content.
- Provide stop/cancel controls, bounded iterations, safe recovery, and clear error reporting. Do not hide failures behind success-shaped responses.
- Protect local endpoints and connector configuration; bind local inference services to loopback by default, authenticate local clients, restrict allowed origins, and bound request size, duration, and concurrency. Require explicit protection before allowing non-loopback binding; loopback alone is not authentication.
- Define and test the supported JSON Schema subset for structured tools. Reject unsupported schema features and invalid arguments explicitly rather than treating partial schema handling as full validation.

## 9. Internet Search and Deep Research

- Provide a search connector and a page-retrieval/reader connector with configurable providers; isolate network access from local file tools.
- Support multi-query research, follow-up searches, source comparison, date/freshness checks, and deduplication within explicit time and token budgets.
- Cite claims with direct source links and distinguish primary sources from secondary summaries.
- Identify missing, inaccessible, stale, or contradictory evidence rather than inventing citations or presenting uncertainty as fact.
- Keep web content in a separate untrusted context; web pages cannot directly invoke local tools.
- Make internet use opt-in per session or per request, show the selected provider, and do not transmit workspace context unless the user specifically approves it.

## 10. Hardware-Aware Engineering and Optimization

TAEL should help users build software that fits its target environment, not only run its own model efficiently. It should be able to:

- Ask about or inspect user-approved target constraints such as CPU, memory, storage, OS, power, and available accelerators.
- Prefer suitable algorithms, data structures, dependencies, concurrency models, and deployment options for the stated target.
- Estimate costs first, then use profiling and measurements where available; state assumptions and measured uncertainty.
- Offer options such as reducing allocations, streaming data, batching, caching, smaller dependencies, and graceful degradation.
- Run benchmarks only within explicit resource limits and report before/after results with the test conditions.
- Avoid starting resource-intensive builds, indexing, or parallel jobs when the supervisor detects memory pressure.

## 11. 8GB RAM and CPU-Only Resource Budget

The 8GB system requirement is a design constraint, not a promise that every Windows installation has the same free memory. TAEL must check real conditions at startup and adapt.

- Measure total and available RAM, relevant TAEL/Aider/model process working sets, CPU load, and context/KV-cache use.
- Define configurable profiles such as **Conservative (8GB CPU-only)** and **Balanced (higher-memory systems)**.
- On the 8GB profile, keep only one primary inference model loaded, bound context and output sizes, limit CPU threads, avoid simultaneous indexing/building, and unload or pause idle services where supported.
- Reserve configurable headroom for the operating system and foreground applications. Reduce context, pause nonessential work, or ask before proceeding when headroom is low.
- Set per-tool time, output, process, and concurrency limits; provide cancellation and ensure timed-out child processes are cleaned up.
- Distinguish resource telemetry and adaptive heuristics from enforced limits. Enforce process/runtime budgets where the platform supports it, and describe any best-effort controls accurately.
- Use incremental, ignored-file-aware indexing with a size cap, cache invalidation, and an explicit pause/clear option.
- Clearly report resource use and the reason for any throttling. Never promise that the host will stay below a fixed RAM ceiling without measuring it.

**Initial performance targets (to be validated and adjusted from real measurements):**

- Complete local coding and chat tasks without requiring a GPU or a cloud inference service.
- Keep TAEL's additional non-model idle footprint small; publish separate measurements for the model, runtime, Aider, UI, and optional indexing.
- On supported 8GB reference laptops, avoid sustained system-wide memory pressure and recover gracefully when other applications reduce available RAM.
- Establish CPU latency/throughput baselines for short prompts, code edits, and long-context tasks rather than promising V2's token rates for a different model.

## 12. Quality, Testing, and Success Metrics

V3 uses a public, versioned evaluation set with fixed prompts, expected outputs or executable checks, machine details, model quantization, runtime settings, and raw per-case results. Separate automated correctness from qualitative review.

- **Software task success:** Measure task completion, test/build pass rate, regression rate, and human-reviewed patch quality across multiple languages and project sizes.
- **Tool reliability:** Measure schema-valid calls, successful execution, correct recovery from errors, cancellation, and policy enforcement.
- **Research quality:** Check citation correctness, claim-to-source support, source diversity, freshness, and appropriate uncertainty.
- **Safety:** Test path escapes, secret access, unsafe commands, prompt injection in files/pages, unapproved app launches, approval bypass, and external side effects. Any critical policy bypass blocks release.
- **Resource behavior:** Measure peak and steady-state RAM, CPU utilization, latency, throughput, indexing footprint, recovery under memory pressure, and operation on multiple representative 8GB CPU-only laptops.
- **User control:** Verify approvals are visible, revocable, correctly scoped, and recorded; verify cancellation halts inference and spawned processes.
- **Honest reporting:** Every published score is traceable to a test case and run configuration. Mark skipped, flaky, qualitative, and partial results explicitly; do not generalize a small test set into a broad 100% accuracy claim.
- **Privacy:** Confirm local inference is the default, outbound requests are visible, and no project content is transmitted without explicit consent.
- **Memory efficiency and quality:** Measure retrieval relevance, stale/conflicting-memory handling, update correctness, and task success against a no-memory baseline. Report memory tokens supplied per task and repeated repository discovery; ensure task context stays within the configured memory budget.

Release targets should be set after a baseline run on the actual Granite Code 3B quantization and selected 8GB reference hardware.

## 13. Implementation Roadmap

### Phase 0: Feasibility and V3 Baseline

- Confirm the exact IBM Granite Code 3B model, license, quantized artifacts, context format, CPU compatibility, and measured memory use.
- Verify model provenance and pinned checksums or signatures before downloading or distributing artifacts.
- Verify Aider can use the selected local inference endpoint for edit, lint/test, and diff-review workflows.
- Establish reference Windows 8GB CPU-only devices and reproducible baseline tasks.
- Decide the initial UI and the supported permission/connector mechanisms.

### Phase 1: Reliable Local Coding Core

- Integrate Aider with local Granite Code 3B and the existing project-aware coding workflow.
- Deliver natural-language plan, repository inspection, focused edits, diff review, test/build iteration, cancellation, and completion reporting.
- Add robust configuration, diagnosable errors, session history, and safe project/worktree handling.
- Preserve the VS Code workflow where useful; define desktop/CLI scope based on Phase 0 results.

### Phase 2: Resource Supervisor and Memory

- Implement live resource measurement, 8GB conservative profile, queueing/backpressure, context controls, and subprocess limits.
- Implement the built-in per-project memory store for TAEL users: local SQLite/FTS5 storage and indexing, compact project profile, categorized/provenance-aware entries, task-based search with a hard token budget, on-demand search, and focused add/update/supersede operations.
- Add user-facing memory search, inspection, editing, disable/clear, and Markdown import/export controls. Keep this runtime store separate from TAEL's own repository `PROJECT_MEMORY.md`.
- Evaluate retrieval relevance, update quality, stale/conflicting entries, token use, and task outcomes against a no-memory baseline; keep source inspection authoritative over remembered claims.
- Improve context retrieval for larger repositories and validate idle and active memory behavior with Aider, inference, UI, indexing, and tests running together.

### Phase 3: Permissioned Tools and Desktop Integration

- Introduce typed tool schemas, capability grants, approval prompts, audit records, and policy enforcement independent of model output.
- Add safe workspace, test, Git, and selected system-information tools.
- Implement approved application launch first; add bounded UI automation only for supported applications and after scope-specific confirmation.
- Add connector documentation and a reviewed extension mechanism for additional tools/MCP servers.

### Phase 4: Internet Search and Research

- Add user-visible search and page retrieval, source tracking, evidence comparison, and citation generation.
- Enforce network consent, data minimization, untrusted-content boundaries, and bounded research budgets.
- Evaluate research correctness against source-verified questions.

### Phase 5: Hardware-Aware Optimization

- Add profiling/benchmark workflows and target-hardware profiles for user software.
- Provide measured optimization suggestions and safe, reviewable implementation loops.
- Evaluate improvements with reproducible before/after workloads.

### Phase 6: Hardening and Release

- Run multi-device resource and compatibility tests, connector and permission tests, safety/prompt-injection tests, and end-to-end task evaluations.
- Exercise the actual inference engine, daemon/API, and client integration on each supported platform, including tool hand-off across the service boundary, session isolation and archive cleanup, authentication/request limits, cancellation, and clean shutdown. Clearly identify any release checks that remain mocked or untested against the native engine.
- Package a straightforward single-file installer/download where practical, or provide one copy-paste command that installs prerequisites, obtains the selected model with clear size/progress information, configures TAEL, and launches it. Do not require a sequence of manual setup commands for the standard path.
- Ensure the first-run flow handles prerequisites, model download, configuration, and common failures with clear progress and recovery; provide a portable/offline bundle option if its large model size and 8GB hardware constraints make it practical.
- Publish concise beginner quick-start guidance alongside installation, model/runtime setup, privacy, permissions, safety, troubleshooting, supported hardware, and known-limitations documentation.
- Release only when the required safety, resource, and reliability gates pass.

## 14. Initial Scope Boundaries

- The first V3 release prioritizes local software engineering, research, and explicitly approved desktop assistance. It is not an unrestricted remote-control or general-purpose operating-system agent.
- "Can use any tool" means an extensible, user-approved connector ecosystem—not arbitrary code execution with unlimited system, account, or network privileges.
- Internet search is supported, but local model inference remains the default; cloud inference is not silently substituted.
- Hardware-aware engineering includes profiling and optimization within practical user-approved limits; it does not imply guaranteed speedups or automatic changes to device firmware, drivers, or system configuration.
- Aider and Granite Code 3B are the initial coding stack. Additional models or providers are considered only after local resource, privacy, licensing, and quality evaluation.

## 15. Definition of Done

TAEL V3 is ready for an initial release when a user on a documented 8GB CPU-only laptop can:

1. Install and start TAEL using one downloadable installer/package or one documented setup-and-launch command, without a manual chain of setup steps.
2. Complete first-run setup with clear guidance and progress, including model acquisition, and understand storage, internet, and hardware requirements before committing to large downloads.
3. Install and run the application with IBM Granite Code 3B locally through the supported Aider integration.
4. Describe a software task in natural language and receive a reviewable implementation with truthful test/build results.
5. Use TAEL's built-in, persistent per-project memory: the agent retrieves task-relevant context within a token budget, updates useful knowledge between tasks, and the user can inspect, edit, export, disable, or delete it.
6. Conduct a permissioned internet research task and receive source-linked findings with uncertainty represented honestly.
7. Approve or reject requested application launches and other sensitive actions, with no unapproved action taking place.
8. Stop a running task and see resource use, tool activity, errors, and any incomplete work.
9. Pass the release's reproducible usability, software, research, safety, privacy, and 8GB resource evaluation gates, including a first-time-user installation test.
