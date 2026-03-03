.PHONY: fmt lint check

fmt:
	uvx ruff format skills/

lint:
	uvx ruff check skills/

check: fmt lint
