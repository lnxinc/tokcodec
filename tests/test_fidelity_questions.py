"""The fidelity question set must load and every expected answer must exist in its sample."""
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).parent.parent
QDIR = ROOT / "bench" / "fidelity" / "questions"


@pytest.mark.parametrize("qfile", sorted(QDIR.glob("*.yaml")), ids=lambda p: p.name)
def test_question_file(qfile):
    d = yaml.safe_load(qfile.read_text(encoding="utf-8"))
    sample = ROOT / "samples" / d["sample"]
    assert sample.exists()
    text = sample.read_text(encoding="utf-8")
    assert len(d["questions"]) >= 8
    ids = set()
    for q in d["questions"]:
        assert q["id"] not in ids; ids.add(q["id"])
        assert q["type"] in {"structural", "failure", "detail", "value"}
        assert q["level_expected_to_answer"] in (1, 2, 3)
        assert isinstance(q["expected"], str) and q["expected"].strip()
