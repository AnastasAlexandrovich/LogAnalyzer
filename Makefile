# Makefile
.PHONY: lint check-code test test-cov
lint:
	pre-commit run --all-files

check-code:
	black loganalyzer/loganalyzer.py
	flake8 loganalyzer/loganalyzer.py

test:
	pytest loganalyzer/test/loganalyzer-test.py

test-cov:
	pytest tests --cov=. --cov-config=tests/.coveragerc --cov-report term
