"""
TAEL V3 — End-to-End Programmatic Agent Workflow Demo
This script demonstrates:
1. Loading configuration with hardware supervisor profiling.
2. In-product persistent project memory storage and FTS5 retrieval.
3. Multi-turn task orchestration with tools.
4. Workspace safety snapshots.
5. Algorithmic profiling with ProfileCommandTool.
"""
from pathlib import Path
from tael.config.settings import TaelConfig
from tael.core.orchestrator import TaskOrchestrator, OrchestratorProgress
from tael.memory.models import MemoryCategory
from tael.memory.store import MemoryStore
from tael.policy.rollback import SnapshotManager
from tael.resources.monitor import ResourceMonitor
from tael.tools.profiler import ProfileCommandTool


class DemoProgress(OrchestratorProgress):
    def on_thought(self, content: str) -> None:
        print(f"\n[TAEL Thought]:\n{content}")

    def on_tool_start(self, tool_name: str, args: dict) -> None:
        print(f"  -> [Tool Start]: {tool_name} with {args}")

    def on_tool_end(self, tool_name: str, result_summary: str, success: bool) -> None:
        status = "OK" if success else "FAILED"
        print(f"  <- [Tool End]: {tool_name} [{status}]: {result_summary[:100]}...")


def run_demo():
    print("=== TAEL V3 End-to-End Workflow Demonstration ===")

    # 1. Initialize configuration & resource supervisor
    config = TaelConfig.load()
    monitor = ResourceMonitor(config.resource.profile)
    snapshot = monitor.sample()
    print(f"\n1. Hardware Profile: {snapshot.active_profile.upper()}")
    print(f"   RAM: {snapshot.available_ram_gb} GB free / {snapshot.total_ram_gb} GB total (Load: {snapshot.ram_percent}%)")

    # 2. In-Product Persistent Project Memory
    memory_store = MemoryStore(config.workspace_root, config.memory.store_dir)
    print("\n2. Storing Architecture Decision in Project Memory...")
    entry = memory_store.add_entry(
        category=MemoryCategory.ARCHITECTURE,
        title="SQLite Offline Storage Schema",
        content="Use single-file SQLite database with WAL mode and autocommit transactions for offline resilience.",
        tags=["sqlite", "offline", "storage"],
        source_paths=["examples/inventory_app/inventory.py"],
        verified=True,
    )
    print(f"   Stored Entry ID #{entry.id}: '{entry.title}'")

    print("\n   Querying Memory via FTS5 BM25 search for 'sqlite'...")
    search_results = memory_store.search_fts("sqlite", limit=3)
    for r in search_results:
        print(f"   - Match: [{r.category.value}] {r.title} (Verified: {r.verified})")

    # 3. Create Safety Checkpoint
    snapshot_mgr = SnapshotManager(config.workspace_root)
    chk = snapshot_mgr.create_checkpoint("Before running demo inventory task")
    print(f"\n3. Created Safety Checkpoint: {chk.id} ({chk.description})")

    # 4. Run Task via Orchestrator
    orchestrator = TaskOrchestrator(config)
    print("\n4. Running Task via Orchestrator...")
    task_prompt = "List the files in examples/inventory_app and verify what functions are defined."
    result = orchestrator.execute_task(task_prompt, progress=DemoProgress(), max_turns=3)

    print(f"\n   Task Status: {result['status']}")
    print(f"   Turns: {result['turns']} | Duration: {result['duration_seconds']}s")
    print(f"   Final Answer:\n{result['final_answer']}")

    # 5. Profile a Command
    profiler = ProfileCommandTool()
    print("\n5. Profiling Python Test Suite Execution...")
    prof_res = profiler.run(
        {"command": "pytest examples/inventory_app/test_inventory.py -q"},
        {"workspace_root": config.workspace_root},
    )
    if prof_res.success:
        data = prof_res.data
        print(f"   Duration: {data['duration_ms']:.1f} ms | Peak RAM: {data['peak_memory_mb']:.2f} MB")
    else:
        print(f"   Profiler error: {prof_res.error}")

    print("\n=== Demo Complete! ===")


if __name__ == "__main__":
    run_demo()
