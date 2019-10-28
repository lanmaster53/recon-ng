FROM python:3.7-alpine

RUN apk add --no-cache --virtual .build-deps gcc libc-dev libxslt-dev && \
    apk add --no-cache libxslt && \
    pip install --no-cache-dir lxml && \
    apk del .build-deps && \
    mkdir -p /recon-ng

WORKDIR /recon-ng

ADD ./REQUIREMENTS /recon-ng/REQUIREMENTS

RUN pip install -r REQUIREMENTS
