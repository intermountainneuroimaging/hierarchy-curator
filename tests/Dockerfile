ARG BASE
FROM ${BASE}
MAINTAINER Flywheel <support@flywheel.io>

ENV FLYWHEEL="/flywheel/v0"

COPY ["tests/requirements.txt", "/opt/requirements.txt"]
RUN pip install -r /opt/requirements.txt 

WORKDIR $FLYWHEEL
