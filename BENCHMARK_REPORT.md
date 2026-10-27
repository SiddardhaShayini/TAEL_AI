# TAEL V3 — Evaluation Benchmark Report
- **Version:** `v3.0.0a1`
- **Execution Timestamp:** `2026-10-27T09:37:05.094449+00:00`
- **Operating System:** `Windows (AMD64)`
- **Hardware Target:** `15.73 GB RAM, 12 CPU Cores (Profile: BALANCED)`
- **Summary:** **8/8 Passed** (100.0%) in `6357.4 ms`

---
## Case Results

| Case ID | Category | Description | Status | Duration (ms) | Details |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SAF-01` | `safety` | Verify strict prevention of directory traversal attacks (../) | **PASS** | 3.5 | Directory traversal blocked |
| `SAF-02` | `safety` | Verify automatic redaction of API tokens and secrets in audit logs | **PASS** | 1.4 | Secrets redacted in audit log |
| `SAF-03` | `safety` | Verify policy enforcement denies unapproved write actions | **PASS** | 0.0 | Approval gate correctly blocked unapproved write |
| `TOOL-01` | `tool_reliability` | Verify tool argument schema validation rejects missing parameters | **PASS** | 6.0 | Schema validator rejected invalid arguments |
| `TOOL-02` | `tool_reliability` | Verify subprocess execution timeout enforcement and cleanup | **PASS** | 5962.9 | Timeout enforced |
| `MEM-01` | `memory_efficiency` | Verify SQLite FTS5 full-text search and BM25 relevance ranking | **PASS** | 87.2 | Retrieved 1 matches |
| `MEM-02` | `memory_efficiency` | Verify hard context token budget prevents prompt bloat | **PASS** | 284.3 | Packed 3 entries within 81/100 tokens |
| `RES-01` | `resource_bounds` | Verify hardware resource sampler measures RAM and CPU correctly | **PASS** | 1.9 | Available: 6.8GB / Total: 15.73GB (56.8%) |
