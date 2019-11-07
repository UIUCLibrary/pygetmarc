FROM python:3.7
ADD ["requirements.txt", "requirements-dev.txt", "/tmp/"]

RUN python -m pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt -r /tmp/requirements-dev.txt