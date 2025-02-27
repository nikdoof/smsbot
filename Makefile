.venv:
	python3 -m pip install poetry
	python3 -m poetry install --with github

.PHONY: tests
tests: .venv
	python3 -m poetry run pytest

lint: .venv
	python3 -m poetry run ruff check --output-format=github --select=E9,F63,F7,F82 --target-version=py37 .
	python3 -m poetry run ruff check --output-format=github --target-version=py37 .

serve-uwsgi:
	SIMPLE_WEBFINGER_CONFIG_FILE="examples/example-config.yaml" python3 -m poetry run gunicorn "simple_webfinger.app:create_app()"

serve:
	DEBUG_METRICS=1 SIMPLE_WEBFINGER_CONFIG_FILE="examples/example-config.yaml" FLASK_DEBUG=1 FLASK_APP="simple_webfinger.app:create_app()" python3 -m poetry run flask run 
