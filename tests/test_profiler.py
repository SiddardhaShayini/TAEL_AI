from tael.tools.profiler import ProfileCommandTool, CompareBenchmarksTool


def test_profile_command_tool():
    tool = ProfileCommandTool()
    # Run a fast python command
    res = tool.run({"command": "python -c \"x = sum(range(100000)); print('done')\""}, {})
    assert res.success is True
    assert res.data["duration_ms"] > 0
    assert "peak_memory_mb" in res.data
    assert res.data["exit_code"] == 0


def test_compare_benchmarks():
    tool = CompareBenchmarksTool()

    # Case 1: Improvement (500ms -> 250ms, 2x speedup)
    res_better = tool.run(
        {
            "baseline_ms": 500.0,
            "optimized_ms": 250.0,
            "baseline_memory_mb": 100.0,
            "optimized_memory_mb": 80.0,
        },
        {},
    )
    assert res_better.success is True
    data = res_better.data
    assert data["is_improvement"] is True
    assert data["speedup_factor"] == 2.0
    assert data["time_change_percent"] == -50.0
    assert data["memory_delta_mb"] == -20.0
    assert "Speedup" in data["summary"]

    # Case 2: Slowdown (100ms -> 150ms)
    res_worse = tool.run({"baseline_ms": 100.0, "optimized_ms": 150.0}, {})
    assert res_worse.success is True
    assert res_worse.data["is_improvement"] is False
    assert "Slowdown" in res_worse.data["summary"]
