FROM python:3.7-alpine3.12

ARG CUSTOM_CRT_URL

ENV TZ=UTC
ENV LIBRDKAFKA_VERSION v1.6.1
ENV BUILD_DEPS git make gcc g++ curl pkgconfig bsd-compat-headers zlib-dev openssl-dev cyrus-sasl-dev curl-dev zstd-dev yajl-dev python3-dev
ENV RUN_DEPS bash libcurl tzdata git curl linux-headers jq cyrus-sasl-gssapiv2 ca-certificates libsasl heimdal-libs krb5 zstd-libs zstd-static yajl python3 py3-pip

RUN apk add --no-cache $RUN_DEPS

RUN \
    apk update && \
    apk add --no-cache --virtual .dev_pkgs $BUILD_DEPS && \
    echo Installing librdkafka && \
    mkdir -p /usr/src/librdkafka && \
    cd /usr/src/librdkafka && \
    curl -LfsS https://github.com/edenhill/librdkafka/archive/${LIBRDKAFKA_VERSION}.tar.gz | \
        tar xvzf - --strip-components=1 && \
    ./configure --prefix=/usr --disable-lz4-ext && \
    make -j && \
    make install && \
    cd / && \
    rm -rf /usr/src/librdkafka && \
    apk del .dev_pkgs

RUN cd /usr/src \
    && git clone https://github.com/JeffersonLab/jaws \
    && cd ./jaws \
    && cp -r scripts /scripts \
    && cd .. \
    && chmod -R +x /scripts/* \
    && cp ./jaws/docker-entrypoint.sh / \
    && chmod +x /docker-entrypoint.sh \
    && apk add --no-cache --virtual .build-deps gcc musl-dev \
    && if [ -z "$CUSTOM_CRT_URL" ] ; then echo "No custom cert needed"; else \
          wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
          && update-ca-certificates \
          && export OPTIONAL_CERT_ARG=--cert=/etc/ssl/certs/ca-certificates.crt \
          ; fi \
    && pip install --no-cache-dir -r ./jaws/requirements.txt $OPTIONAL_CERT_ARG \
    && apk del .build-deps \
    && rm -rf ./jaws

WORKDIR /scripts

ENTRYPOINT ["/docker-entrypoint.sh"]