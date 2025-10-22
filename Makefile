format:
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place prazo --exclude=__init__.py
	black prazo --line-length 80
	isort --profile black prazo --line-length 80

run:
	uv run python -m prazo.main

service:
	frontend/api.py

frontend:
	cd frontend && python -m http.server 3000
