VENV := .venv
PYTHON := $(VENV)/bin/python3

.PHONY: test
test: $(VENV)
	$(PYTHON) -m unittest discover tests/ -v

$(VENV): requirements-test.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -q -r requirements-test.txt
	@touch $(VENV)