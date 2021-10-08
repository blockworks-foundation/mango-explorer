.EXPORT_ALL_VARIABLES:
commands := $(wildcard bin/*)

setup: ## Install all the build and lint dependencies
	pip install -r requirements.txt
	echo "y" | mypy --install-types

upgrade: ## Upgrade all the build and lint dependencies
	pip install --upgrade -r requirements.txt
	echo "y" | mypy --install-types

test: ## Run all the tests
	pytest -rP tests

#cover: test ## Run all the tests and opens the coverage report
#	TODO: Coverage

mypy:
	rm -rf .tmplintdir .mypy_cache
	mkdir .tmplintdir
	for file in bin/* ; do \
        cp $${file} .tmplintdir/$${file##*/}.py ; \
	done
	-mypy --no-incremental --cache-dir=/dev/null mango tests .tmplintdir
	rm -rf .tmplintdir

flake8:
	flake8 --extend-ignore E402,E501,E722,W291,W391 . bin/*

lint: flake8 mypy

ci: lint test ## Run all the tests and code checks

docker-build:
	docker build --build-arg=LAST_COMMIT="`git log -1 --format='%h [%ad] - %s'`" . -t opinionatedgeek/mango-explorer-v3:latest

docker-push:
	docker push opinionatedgeek/mango-explorer-v3:latest

docker: docker-build docker-push

docker-experimental-build:
	docker build --build-arg=LAST_COMMIT="`git log -1 --format='%h [%ad] - %s'`" . -t opinionatedgeek/mango-explorer-v3:experimental

docker-experimental-push:
	docker push opinionatedgeek/mango-explorer-v3:experimental

docker-experimental: docker-experimental-build docker-experimental-push

marketmaker-binary:
	NUITKA_CACHE_DIR=/var/tmp/nuitka python3 -m nuitka --plugin-enable=numpy --plugin-enable=pylint-warnings --include-data-file=data/*=data/ --output-dir=dist --remove-output --standalone --onefile bin/marketmaker


# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
