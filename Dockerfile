FROM python:3.7-alpine

RUN apk add --no-cache --virtual .build-deps gcc libc-dev libxslt-dev && \
    apk add --no-cache libxslt && \
    pip install --no-cache-dir lxml && \
    apk del .build-deps && \
    apk add git && \
    git clone --single-branch --branch staging https://github.com/lanmaster53/recon-ng.git /root/recon-ng

WORKDIR /root/recon-ng

RUN pip install -r REQUIREMENTS

CMD ./recon-ng
