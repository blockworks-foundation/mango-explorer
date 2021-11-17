FROM python:3.9-buster

RUN sh -c "$(curl -sSfL https://release.solana.com/v1.8.4/install)"

RUN apt-get update && apt-get -y install bc curl zlib1g-dev

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
ARG LAST_COMMIT=""
RUN echo ${LAST_COMMIT} > /app/data/.version
