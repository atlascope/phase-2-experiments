FROM python:3.9

WORKDIR /atlascope

COPY ./requirements.txt /atlascope/requirements.txt

RUN pip install --no-cache-dir -r /atlascope/requirements.txt
