.PHONY: help default docs test black
.DEFAULT_GOAL := default
PROJECT := tea

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


default:
	python -m "$(PROJECT)"


docs:
	cd docs && make html
	open docs/_build/html/index.html


test:
	py.test --pep8 "$(PROJECT)" --cov "$(PROJECT)" --flake8 "$(PROJECT)" --docstyle "$(PROJECT)"


black:
	@black --line-length 79 --safe "$(PROJECT)"
