import os
import shutil
from pathlib import Path
from typing import Optional
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from tael import __version__
from tael.config.settings import TaelConfig
from tael.models.runtime import ModelRuntimeManager
from tael.resources.monitor import ResourceMonitor

console = Console()


def run_onboarding_wizard(config: Optional[TaelConfig] = None, interactive: bool = True) -> TaelConfig:
    """Run an approachable first-run setup wizard that checks hardware, explains local AI requirements, and configures TAEL."""
    cfg = config or TaelConfig.load()
    monitor = ResourceMonitor()
    snapshot = monitor.sample()
    runtime = ModelRuntimeManager(cfg.model)

    console.print(Panel(
        f"[bold green]Welcome to TAEL AI (v{__version__})[/bold green]\n"
        f"[italic]\"Capable local AI, built for everyday hardware.\"[/italic]\n\n"
        f"This setup wizard will inspect your system, check local model prerequisites,\n"
        f"and configure optimal resource limits for your machine.",
        border_style="green",
    ))

    # 1. Hardware Inspection & Profile Selection
    console.print("\n[bold cyan]Step 1: Hardware Inspection[/bold cyan]")
    hw_table = Table(title="Detected Hardware Specifications")
    hw_table.add_column("Component", style="cyan")
    hw_table.add_column("Measurement", style="bold yellow")
    hw_table.add_column("Assessment", style="green")

    hw_table.add_row(
        "Total System RAM",
        f"{snapshot.total_ram_gb} GB",
        "8GB Target Machine" if snapshot.total_ram_gb <= 10.0 else "Workstation / Laptop (16GB+)",
    )
    hw_table.add_row(
        "Available Free RAM",
        f"{snapshot.available_ram_gb} GB",
        f"{100 - snapshot.ram_percent:.1f}% free",
    )
    hw_table.add_row(
        "CPU Cores",
        f"{snapshot.cpu_count_logical} logical ({snapshot.cpu_count_physical} physical)",
        "Multi-core CPU execution",
    )

    recommended_profile = "conservative" if snapshot.total_ram_gb <= 10.0 else "balanced"
    hw_table.add_row(
        "Recommended Profile",
        recommended_profile.upper(),
        "4096 tokens, bounded threads" if recommended_profile == "conservative" else "8192 tokens",
    )
    console.print(hw_table)

    cfg.resource.profile = recommended_profile

    # 2. Local Inference Runtime Check (Ollama & Granite Code 3B)
    console.print("\n[bold cyan]Step 2: Local Model Runtime Check[/bold cyan]")
    ollama_online = runtime.check_health()
    installed_models = runtime.list_installed_models() if ollama_online else []
    granite_present = any("granite-code" in m for m in installed_models)

    rt_table = Table(title="Model Engine Status")
    rt_table.add_column("Component", style="cyan")
    rt_table.add_column("Status", style="bold")
    rt_table.add_column("Details", style="white")

    rt_table.add_row(
        "Ollama Local Server",
        "[green]ONLINE[/green]" if ollama_online else "[yellow]NOT DETECTED[/yellow]",
        f"Loopback endpoint: {cfg.model.endpoint}",
    )
    rt_table.add_row(
        "Target Model",
        "[green]INSTALLED[/green]" if granite_present else "[yellow]NOT INSTALLED[/yellow]",
        f"{cfg.model.model_name} (~2.0 GB download)",
    )

    aider_installed = shutil.which("aider") is not None
    rt_table.add_row(
        "Aider Coding Engine",
        "[green]AVAILABLE[/green]" if aider_installed else "[yellow]NOT DETECTED[/yellow]",
        "Found on system PATH" if aider_installed else "Optional: pip install aider-chat",
    )
    console.print(rt_table)

    if not ollama_online:
        console.print(
            "\n[yellow]Notice:[/yellow] Ollama is not running on 127.0.0.1:11434.\n"
            "To use local Granite inference, download and run Ollama from [cyan]https://ollama.com[/cyan].\n"
            "Once running, pull the model with: [bold green]ollama pull granite-code:3b[/bold green]\n"
            "(TAEL includes offline mock mode and will work with all tools in the meantime)."
        )

    # 3. Privacy & Approval Policy
    console.print("\n[bold cyan]Step 3: Security & Privacy Policy[/bold cyan]")
    console.print(
        "TAEL runs inference locally by default. File modifications and shell commands\n"
        "require explicit user approval before execution. Internet access is opt-in."
    )

    # 4. Save Configuration
    tael_dir = Path(cfg.workspace_root) / ".tael"
    tael_dir.mkdir(parents=True, exist_ok=True)
    config_file = tael_dir / "config.yaml"

    export_data = {
        "model": cfg.model.model_dump(),
        "resource": cfg.resource.model_dump(),
        "policy": cfg.policy.model_dump(),
        "memory": cfg.memory.model_dump(),
        "server": cfg.server.model_dump(),
    }

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(export_data, f, default_flow_style=False)

    console.print(f"\n[bold green]Setup Complete![/bold green] Configuration written to: [cyan]{config_file}[/cyan]")
    console.print("You can now start interactive coding with: [bold yellow]tael chat[/bold yellow]\n")

    return cfg
