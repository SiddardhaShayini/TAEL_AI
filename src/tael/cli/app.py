import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from tael import __version__
from tael.config.settings import TaelConfig
from tael.core.orchestrator import TaskOrchestrator, OrchestratorProgress
from tael.core.session import SessionState
from tael.memory.models import MemoryCategory
from tael.memory.store import MemoryStore
from tael.models.runtime import ModelRuntimeManager
from tael.resources.monitor import ResourceMonitor

console = Console()


class RichProgressHandler(OrchestratorProgress):
    def on_thought(self, content: str) -> None:
        console.print(Panel(content, title="[bold cyan]TAEL[/bold cyan]", border_style="cyan"))

    def on_tool_start(self, tool_name: str, args: dict) -> None:
        console.print(f"[bold yellow]-> Executing Tool:[/bold yellow] [green]{tool_name}[/green]")
        console.print(f"  [dim]Args: {args}[/dim]")

    def on_tool_end(self, tool_name: str, result_summary: str, success: bool) -> None:
        status_color = "green" if success else "red"
        console.print(f"  [{status_color}]Result: {result_summary}[/{status_color}]\n")

    def on_pressure_warning(self, message: str) -> None:
        console.print(f"[bold red]! Warning:[/bold red] [yellow]{message}[/yellow]")


def cmd_status(config: TaelConfig) -> None:
    monitor = ResourceMonitor(config.resource.profile)
    snapshot = monitor.sample()
    runtime = ModelRuntimeManager(config.model)
    ollama_ok = runtime.check_health()
    installed_models = runtime.list_installed_models() if ollama_ok else []

    table = Table(title=f"TAEL V3 System Status (v{__version__})")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Active Workspace", config.workspace_root)
    table.add_row("Resource Profile", f"{snapshot.active_profile.upper()}")
    table.add_row("Total RAM", f"{snapshot.total_ram_gb} GB")
    table.add_row("Available RAM", f"{snapshot.available_ram_gb} GB ({100 - snapshot.ram_percent}% free)")
    table.add_row("RAM Usage", f"{snapshot.ram_percent}%")
    table.add_row("CPU Load", f"{snapshot.cpu_percent}% ({snapshot.cpu_count_logical} logical cores)")
    table.add_row("Under Pressure?", "[red]YES[/red]" if snapshot.is_under_pressure else "[green]NO[/green]")
    if snapshot.pressure_reason:
        table.add_row("Pressure Reason", f"[yellow]{snapshot.pressure_reason}[/yellow]")

    table.add_row("Model Backend", f"{config.model.backend} ({config.model.endpoint})")
    table.add_row("Model Server Online?", "[green]YES[/green]" if ollama_ok else "[red]OFFLINE[/red]")
    table.add_row("Target Model", config.model.model_name)
    table.add_row("Installed Models", ", ".join(installed_models) if installed_models else "None detected")

    store = MemoryStore(config.workspace_root, config.memory.store_dir)
    profile = store.get_or_create_project_profile()
    entries = store.list_entries(active_only=True)
    table.add_row("Project Memory ID", profile.project_id)
    table.add_row("Stored Memory Entries", str(len(entries)))

    console.print(table)


def cmd_chat(config: TaelConfig, initial_prompt: str = None) -> None:
    orchestrator = TaskOrchestrator(config)
    session = SessionState(workspace_root=config.workspace_root)
    progress = RichProgressHandler()

    console.print(Panel(
        f"[bold green]TAEL V3 Interactive Coding Assistant[/bold green]\n"
        f"Workspace: [cyan]{config.workspace_root}[/cyan]\n"
        f"Profile: [magenta]{config.resource.profile}[/magenta] | Target Model: [yellow]{config.model.model_name}[/yellow]\n"
        f"Type [bold red]exit[/bold red] or [bold red]quit[/bold red] to end the session.",
        border_style="green",
    ))

    if initial_prompt:
        console.print(f"\n[bold cyan]User:[/bold cyan] {initial_prompt}\n")
        orchestrator.execute_task(initial_prompt, session=session, progress=progress)

    while True:
        try:
            user_input = console.input("\n[bold cyan]tael>[/bold cyan] ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break

            orchestrator.execute_task(user_input, session=session, progress=progress)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break


def cmd_memory(config: TaelConfig, args: argparse.Namespace) -> None:
    store = MemoryStore(config.workspace_root, config.memory.store_dir)
    action = args.memory_action

    if action == "list":
        entries = store.list_entries(active_only=True)
        if not entries:
            console.print("[yellow]No active memory entries for this project.[/yellow]")
            return
        table = Table(title=f"Project Memory ({len(entries)} entries)")
        table.add_column("ID", style="dim")
        table.add_column("Category", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Verified", style="green")
        table.add_column("Content Preview", style="white")

        for e in entries:
            status = "YES" if e.verified else "NO"
            table.add_row(str(e.id), e.category.value, e.title, status, e.content[:60] + "...")
        console.print(table)

    elif action == "search":
        query = args.query or ""
        results = store.search_fts(query)
        console.print(f"[bold]Search results for '{query}' ({len(results)} matches):[/bold]\n")
        for r in results:
            console.print(r.to_markdown())

    elif action == "export":
        md = store.export_to_markdown()
        out_path = Path.cwd() / "PROJECT_MEMORY_EXPORT.md"
        out_path.write_text(md, encoding="utf-8")
        console.print(f"[green]Successfully exported project memory to: {out_path}[/green]")

    elif action == "clear":
        count = store.clear_project_memory()
        console.print(f"[red]Cleared {count} memory entries for project {store.project_id}.[/red]")


def cmd_research(config: TaelConfig, query: str) -> None:
    from tael.research.tools import SearchWebTool
    console.print(Panel(f"[bold cyan]Researching:[/bold cyan] {query}", border_style="cyan"))
    tool = SearchWebTool()
    res = tool.run({"query": query, "max_results": 5}, {"workspace_root": config.workspace_root})
    if not res.success:
        console.print(f"[red]Research query failed: {res.error}[/red]")
        return
    results = res.data.get("results", [])
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    table = Table(title=f"Search Findings ({len(results)} sources)")
    table.add_column("Title", style="bold green")
    table.add_column("Source Domain", style="dim")
    table.add_column("Snippet Preview", style="white")
    for r in results:
        table.add_row(r["title"][:40], r["domain"], r["snippet"][:100] + "...")
    console.print(table)


def cmd_profile(config: TaelConfig, command: str) -> None:
    from tael.tools.profiler import ProfileCommandTool
    console.print(Panel(f"[bold magenta]Profiling Command:[/bold magenta] {command}", border_style="magenta"))
    tool = ProfileCommandTool()
    res = tool.run({"command": command}, {"workspace_root": config.workspace_root})
    if not res.success:
        console.print(f"[red]Profiling failed: {res.error}[/red]")
        return
    data = res.data
    table = Table(title="Benchmark Measurements")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold yellow")
    table.add_row("Execution Time", f"{data['duration_ms']:.2f} ms")
    table.add_row("Peak Memory (RSS)", f"{data['peak_memory_mb']:.2f} MB")
    table.add_row("Exit Code", str(data["exit_code"]))
    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(prog="tael", description="TAEL V3: Local-First AI Creation & Research Assistant")
    parser.add_argument("--version", action="version", version=f"tael {__version__}")
    parser.add_argument("--workspace", "-w", help="Workspace root directory (defaults to current dir)")
    subparsers = parser.add_subparsers(dest="command")

    # tael status
    subparsers.add_parser("status", help="Show hardware, resource, and model status")

    # tael chat [PROMPT]
    chat_parser = subparsers.add_parser("chat", help="Start chat session or run single task")
    chat_parser.add_argument("prompt", nargs="?", default=None, help="Optional initial task prompt")

    # tael memory
    mem_parser = subparsers.add_parser("memory", help="Inspect and manage persistent project memory")
    mem_sub = mem_parser.add_subparsers(dest="memory_action")
    mem_sub.add_parser("list", help="List all active memory entries")
    search_parser = mem_sub.add_parser("search", help="Search memory via FTS5")
    search_parser.add_argument("query", help="Search query")
    mem_sub.add_parser("export", help="Export memory to Markdown file")
    mem_sub.add_parser("clear", help="Clear all memory for this project")

    # tael research <query>
    res_parser = subparsers.add_parser("research", help="Search internet and synthesize technical research")
    res_parser.add_argument("query", help="Research query")

    # tael profile <command>
    prof_parser = subparsers.add_parser("profile", help="Profile command execution time and peak memory")
    prof_parser.add_argument("command_str", help="Command to profile")

    args = parser.parse_args()

    config = TaelConfig.load()
    if args.workspace:
        config.workspace_root = str(Path(args.workspace).resolve())

    if args.command == "status":
        cmd_status(config)
    elif args.command == "chat":
        cmd_chat(config, args.prompt)
    elif args.command == "memory":
        cmd_memory(config, args)
    elif args.command == "research":
        cmd_research(config, args.query)
    elif args.command == "profile":
        cmd_profile(config, args.command_str)
    else:
        # Default action: if prompt given, chat; otherwise show status
        cmd_status(config)


if __name__ == "__main__":
    main()
