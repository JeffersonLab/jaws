FROM python:3.7-alpine3.12

ARG CUSTOM_CRT_URL

RUN apk add --no-cache librdkafka git bash curl jq \
    && git clone https://github.com/JeffersonLab/kafka-alarm-system \
    && cd ./kafka-alarm-system \
    && cp -r scripts /scripts \
    && cp -r schemas /schemas \
    && cp -r plugins /plugins \
    && cd ../.. \
    && chmod -R +x /scripts/* \
    && cp ./kafka-alarm-system/docker-entrypoint.sh / \
    && chmod +x /docker-entrypoint.sh \
    && apk add --no-cache --virtual .build-deps gcc musl-dev librdkafka-dev \
    && if [ -z "$CUSTOM_CRT_URL" ] ; then echo "No custom cert needed"; else \
          wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
          && update-ca-certificates \
          && export OPTIONAL_CERT_ARG=--cert=/etc/ssl/certs/ca-certificates.crt \
          ; fi \
    && pip install --no-cache-dir -r ./kafka-alarm-system/requirements.txt $OPTIONAL_CERT_ARG \
    && apk del .build-deps git \
    && rm -rf ./kafka-alarm-system

WORKDIR /scripts

ENTRYPOINT ["/docker-entrypoint.sh"]