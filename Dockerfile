FROM python:3.9-buster

RUN sh -c "$(curl -sSfL https://release.solana.com/v1.8.1/install)"

RUN apt-get update && apt-get -y install bc ccache chrpath libfuse2 zlib1g-dev

RUN mkdir /app
COPY ./pyproject.toml ./poetry.lock ./

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:/app
ENV PATH="/app/built/liquidator.dist:/app/bin:${PATH}:/app/scripts:/root/.local/share/solana/install/active_release/bin"

RUN pip install --upgrade pip && pip --no-cache-dir install poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-root

ARG LAST_COMMIT=""
RUN echo ${LAST_COMMIT} > /app/.version

# Have this as the last step since the code here is the most-frequently changing
COPY . /app/
ENV NUITKA_CACHE_DIR=/var/tmp/nuitka
RUN python3 -m nuitka --plugin-enable=numpy --plugin-enable=pylint-warnings --assume-yes-for-downloads --include-data-file=data/*=data/ --output-dir=built --remove-output --standalone bin/liquidator