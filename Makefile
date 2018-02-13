.PHONY: clean docs build sdist wheel
PYTHON := python3

build: venv
	venv/bin/python setup.py build

wheel: venv
	venv/bin/python setup.py bdist_wheel

sdist: venv
	venv/bin/python setup.py sdist

venv:
	$(PYTHON) -m venv venv
	venv/bin/python -m pip install -r requirements.txt
	venv/bin/python -m pip install -r requirements-dev.txt

clean:
	@$(PYTHON) setup.py clean
	@cd docs && $(MAKE) clean

	@echo "removing '.tox'"
	@rm -rf .tox

	@echo "removing '.eggs'"
	@rm -rf .eggs

	@echo "removing 'uiucprescon_getmarc.egg-info'"
	@rm -rf uiucprescon_getmarc.egg-info

	@echo "removing '.mypy_cache'"
	@rm -rf .mypy_cache

	@echo "removing '.pytest_cache'"
	@rm -rf .pytest_cache


docs: venv
	@echo building docs
	@source venv/bin/activate && cd docs && $(MAKE) html
