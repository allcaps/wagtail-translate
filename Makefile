PYTHON_VERSION ?= 3.14
PYTHON ?= .venv/bin/python
RUFF ?= .venv/bin/ruff
DJLINT ?= .venv/bin/djlint
NPM ?= npm

install:
	uv venv --python $(PYTHON_VERSION)
	uv pip install --python $(PYTHON) -e ".[test,llm,deepl]"

fix-codestyle:
	$(RUFF) check --exit-zero --fix src tests
	$(RUFF) format src tests
	$(DJLINT) tests/testproject --reformat --warn

test:
	$(PYTHON) tests/testproject/manage.py check
	$(PYTHON) tests/testproject/manage.py makemigrations --check --dry-run
	$(DJLINT) tests/testproject --lint --check
	$(RUFF) check src tests
	$(RUFF) format src tests --check
	$(PYTHON) -X dev -m pytest $(ARGS)
