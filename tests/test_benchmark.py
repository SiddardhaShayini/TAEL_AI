from tael.config.settings import TaelConfig
from tael.eval.benchmark import BenchmarkRunner


def test_benchmark_runner_suite():
    cfg = TaelConfig.load()
    runner = BenchmarkRunner(cfg)
    report = runner.run_suite(category="safety")

    assert report.total_cases >= 3
    assert report.passed_cases == report.total_cases
    assert report.pass_rate == 100.0

    # Markdown export test
    md = report.to_markdown()
    assert "# TAEL V3 — Evaluation Benchmark Report" in md
    assert "SAF-01" in md

    # JSON export test
    json_str = report.to_json()
    assert '"pass_rate_percent": 100.0' in json_str
