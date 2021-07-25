.PHONY: help default test fmt check docs docs-commit build release
.DEFAULT_GOAL := help
PROJECT := tea


help:                    ## Show help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


test:                    ## Run tests.
	py.test --cov "$(PROJECT)"


fmt:                     ## Format the code.
	@black --target-version=py37 --safe --line-length 79 "$(PROJECT)"


check:                   ## Run code checkers.
	@flake8 "$(PROJECT)"
	@pydocstyle "$(PROJECT)"


docs:                    ## Build documentation.
	@cd docs && make html && open _build/html/index.html


docs-commit:             ## Build and commit documentation to gh-pages branch.
	@rm -fr docs/_build/html
	@cd docs && make html && ghp-import _build/html

build:                   ## Build the source and wheel distribution packages.
	@python setup.py sdist bdist_wheel


release: build           ## Build and upload the package to PyPI.
	@twine upload --skip-existing  dist/*
	@rm -fr build dist "$(PROJECT).egg-info"
