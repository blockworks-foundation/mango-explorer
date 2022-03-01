FROM python:3.10-slim

RUN apt-get update && apt-get -y install bc curl zlib1g-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
COPY ./pyproject.toml ./poetry.lock ./

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:/app
ENV PATH="/app/bin:${PATH}:/app/scripts:/root/.local/share/solana/install/active_release/bin"

RUN pip install --upgrade pip && pip --no-cache-dir install poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-root

# Have these as the last steps since the code here is the most-frequently changing
COPY . /app/
RUN python3 -m compileall /app
ARG LAST_COMMIT=""
RUN echo ${LAST_COMMIT} > /app/data/.version
