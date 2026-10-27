from tael.resources.profiles import select_profile, CONSERVATIVE_PROFILE, BALANCED_PROFILE
from tael.resources.monitor import ResourceMonitor


def test_profile_selection():
    # 8GB laptop must select conservative profile
    prof_8gb = select_profile("auto", total_ram_gb=7.8)
    assert prof_8gb.name == "conservative"
    assert prof_8gb.max_context_tokens == 4096
    assert prof_8gb.allow_parallel_tools is False

    # 16GB laptop selects balanced profile
    prof_16gb = select_profile("auto", total_ram_gb=15.9)
    assert prof_16gb.name == "balanced"
    assert prof_16gb.max_context_tokens == 8192

    # Explicit override works
    prof_override = select_profile("conservative", total_ram_gb=32.0)
    assert prof_override.name == "conservative"


def test_resource_monitor_sampling():
    monitor = ResourceMonitor(requested_profile="conservative")
    snapshot = monitor.sample()
    assert snapshot.total_ram_gb > 0
    assert snapshot.available_ram_gb > 0
    assert 0 <= snapshot.ram_percent <= 100
    assert snapshot.cpu_count_logical >= 1
    assert snapshot.active_profile == "conservative"
