FROM python:3.8-alpine

ARG CUSTOM_CRT_URL

COPY ./scripts /scripts

WORKDIR /scripts

RUN apk add --no-cache --virtual .build-deps gcc musl-dev librdkafka librdkafka-dev \
    && if [ -z "$CUSTOM_CRT_URL" ] ; then echo "No custom cert needed"; else \
          wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
          && update-ca-certificates \
          && export OPTIONAL_CERT_ARG=--cert=/etc/ssl/certs/ca-certificates.crt \
          ; fi \
    && pip install --no-cache-dir -r requirements.txt $OPTIONAL_CERT_ARG \
    && apk del .build-deps

ENTRYPOINT ["sh"]