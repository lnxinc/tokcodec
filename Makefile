.PHONY: test bench smoke check-versions
test:
	uv run pytest -q
bench:
	uv run python bench/run.py
smoke:
	uv run scripts/smoke.sh
check-versions:
	uv run python scripts/check_versions.py
