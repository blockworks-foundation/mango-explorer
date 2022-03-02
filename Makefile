.EXPORT_ALL_VARIABLES:
commands := $(wildcard bin/*)

setup: ## Install all the build and lint dependencies
	pip --no-cache-dir install poetry
	poetry install --no-interaction

upgrade: ## Upgrade all the build and lint dependencies
	poetry upgrade --no-interaction

test: ## Run all the tests and calculate code coverage
	SOLENV_NAME= SOLENV_ADDRESS= CLUSTER_NAME= CLUSTER_URL= KEYPAIR= PYTEST_ADDOPTS="-p no:cacheprovider" poetry run pytest -rP tests/ --cov=mango

black:
	poetry run black --check mango tests bin/*

flake8:
	poetry run flake8 --extend-ignore E402,E501,E722,W291,W391 . bin/*

mypy:
	bash -c "trap 'trap - SIGINT SIGTERM ERR; rm -rf .tmplintdir .mypy_cache; exit 1' SIGINT SIGTERM ERR; $(MAKE) mypy-internal"

# This target is separated out as an internal so the above line can trap errors and perform
# the cleanup while still returning an error code to the shell so callers know it failed.
mypy-internal:
	rm -rf .tmplintdir .mypy_cache
	mkdir .tmplintdir
	for file in bin/* ; do \
		cp $${file} .tmplintdir/$${file##*/}.py ; \
	done
	poetry run mypy --strict --install-types --non-interactive mango tests .tmplintdir
	rm -rf .tmplintdir .mypy_cache

lint: black flake8 mypy

ci: test lint ## Run all the tests and code checks

package: test lint
	poetry build

publish-package:
	poetry publish

docker-build:
	docker build --build-arg=LAST_COMMIT="`git log -1 --format='%h [%ad] - %s'`" --platform linux/amd64 . -t opinionatedgeek/mango-explorer-v3:latest

docker-push:
	docker push opinionatedgeek/mango-explorer-v3:latest

docker: docker-build docker-push

docker-experimental-build:
	docker build --build-arg=LAST_COMMIT="`git log -1 --format='%h [%ad] - %s'`" --platform linux/amd64 . -t opinionatedgeek/mango-explorer-v3:experimental

docker-experimental-push:
	docker push opinionatedgeek/mango-explorer-v3:experimental

docker-experimental: docker-experimental-build docker-experimental-push

marketmaker-binary:
	NUITKA_CACHE_DIR=/var/tmp/nuitka python3 -m nuitka --plugin-enable=numpy --plugin-enable=pylint-warnings --include-data-file=data/*=data/ --output-dir=dist --remove-output --standalone --onefile bin/marketmaker


# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
