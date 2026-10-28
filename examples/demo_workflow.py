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

    try:
        # 2. In-Product Persistent Project Memory
        memory_store = MemoryStore(config.workspace_root, config.memory.store_dir)
        existing = [e for e in memory_store.list_entries(category=MemoryCategory.ARCHITECTURE) if e.title == "SQLite Offline Storage Schema"]
        if not existing:
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
        else:
            print(f"\n2. Found existing Architecture Decision #{existing[0].id} in Project Memory.")

        print("\n   Querying Memory via FTS5 BM25 search for 'sqlite'...")
        search_results = memory_store.search_fts("sqlite", limit=3)
        for r in search_results:
            print(f"   - Match: [{r.category.value}] {r.title} (Verified: {r.verified})")

        # 3. Create Safety Checkpoint on reference inventory application
        inventory_dir = str(Path(config.workspace_root) / "examples" / "inventory_app")
        snapshot_mgr = SnapshotManager(inventory_dir)
        chk = snapshot_mgr.create_checkpoint("Before running demo inventory task")
        print(f"\n3. Created Safety Checkpoint: {chk.id} ({chk.description})")

        # 4. Run Task via Orchestrator
        orchestrator = TaskOrchestrator(config)
        print("\n4. Running Task via Orchestrator...")
        task_prompt = "List the files in examples/inventory_app and verify what functions are defined."
        result = orchestrator.execute_task(task_prompt, progress=DemoProgress(), max_turns=3)

        status = result.get("status", "completed")
        turns = result.get("turns", 0)
        dur = result.get("duration_seconds", 0)
        final_answer = result.get("final_answer", "")
        print(f"\n   Task Status: {status}")
        print(f"   Turns: {turns} | Duration: {dur}s")
        print(f"   Final Answer:\n{final_answer}")

        # 5. Profile a Command
        import sys
        profiler = ProfileCommandTool()
        print("\n5. Profiling Python Test Suite Execution...")
        prof_res = profiler.run(
            {"command": f"{sys.executable} -m pytest examples/inventory_app/test_inventory.py -q"},
            {"workspace_root": config.workspace_root},
        )
        if prof_res.success:
            data = prof_res.data
            print(f"   Duration: {data['duration_ms']:.1f} ms | Peak RAM: {data['peak_memory_mb']:.2f} MB")
        else:
            print(f"   Profiler error: {prof_res.error}")

        print("\n=== Demo Complete! ===")
    finally:
        print("\n6. Reclaiming RAM (unloading model and stopping background runner)...")
        from tael.models.runtime import ModelRuntimeManager
        runtime = ModelRuntimeManager(config.model)
        unloaded = runtime.unload_model()
        if unloaded:
            print("   Model evicted from RAM and background llama runner terminated. Zero lingering memory.")


if __name__ == "__main__":
    run_demo()
