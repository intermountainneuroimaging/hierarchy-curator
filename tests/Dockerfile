ARG BASE

FROM ${BASE}

ENV FLYWHEEL="/flywheel/v0"

# Install dev dependencies
RUN poetry install

COPY tests ./tests

ENTRYPOINT [""]
