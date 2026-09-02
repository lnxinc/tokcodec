.PHONY: test bench smoke check-versions
test:
	uv run pytest -q
bench:
	uv run python bench/run.py
	uv run python bench/compare.py
bench-exact:
	uv run python bench/run.py --exact
	uv run python bench/compare.py
smoke:
	uv run scripts/smoke.sh
check-versions:
	uv run python scripts/check_versions.py
