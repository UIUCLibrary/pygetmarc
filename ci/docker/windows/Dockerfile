# escape=`

ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}

RUN certutil -generateSSTFromWU roots.sst ; certutil -addstore -f root roots.sst ; del roots.sst
ENV PIP_DOWNLOAD_CACHE=c:\pip_cache

ADD requirements.txt requirements-dev.txt c:\temp\

RUN python -m pip install pip --upgrade ; `
    pip install --extra-index-url https://devpi.library.illinois.edu/production/release `
        --trusted-host devpi.library.illinois.edu `
        -r c:\temp\requirements.txt `
        -r c:\temp\requirements-dev.txt `
        pytest-cov flake8

