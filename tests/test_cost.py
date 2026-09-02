import subprocess
import sys
from pathlib import Path

from tokcodec.pricing import PRICES_PER_MTOK, cost, cost_line

ROOT = Path(__file__).parent.parent


def test_cost_math_and_line():
    assert cost(1_000_000, "claude-sonnet-5") == PRICES_PER_MTOK["claude-sonnet-5"]
    line = cost_line(1_000_000, 100_000)
    assert "opus-5: $5.0000→$0.5000" in line and "sonnet-5: $2.0000→$0.2000" in line


def test_cli_cost_flag_prints_per_model_line():
    r = subprocess.run([sys.executable, "-m", "tokcodec.cli", str(ROOT / "samples" / "pytest_run.log"), "-l", "3", "--cost"],
                       capture_output=True, text=True, check=True, encoding="utf-8")
    assert "[cost per read" in r.stderr and "opus-5: $" in r.stderr and "proxy" in r.stderr


def test_compare_script_reproduces_readme_block(tmp_path):
    """compare.py must regenerate exactly what is committed (CI checks the same)."""
    before = (ROOT / "README.md").read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "bench" / "compare.py")], check=True, capture_output=True)
    assert (ROOT / "README.md").read_text(encoding="utf-8") == before
    assert (ROOT / "bench" / "ESTIMATE-VS-ACTUAL.md").exists()
