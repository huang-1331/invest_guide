.PHONY: test probe collect run notebook
export PYTHONPATH := $(CURDIR)/src

test:
	python -m pytest -q tests
probe:
	python -m capitalrisk.pipeline probe
collect:
	python -m capitalrisk.pipeline collect
run:
	python -m capitalrisk.pipeline run
notebook:
	python scripts/execute_notebook.py
