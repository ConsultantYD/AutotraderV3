uv_install:
	uv sync
	uv pip install -r requirements.txt
	uv pip install -e .

pip_install:
	pip install -r requirements.txt
	pip install -e .
	
export_dependencies:
	uv pip compile pyproject.toml -o requirements.txt

format:
	uvx ruff format autotrader
	uvx ruff format tests

lint:
	uvx ruff check autotrader
	uvx ruff check tests

security_scan:
	uv run bandit -r autotrader -s B403,B301,B311

unit_test:
	pytest tests/