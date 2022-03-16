ARG BUILD_IMAGE=python:3.9-alpine3.15
ARG RUN_IMAGE=python:3.9-alpine3.15
ARG VIRTUAL_ENV=/opt/venv

################## Stage 0
FROM ${BUILD_IMAGE} as builder
ARG CUSTOM_CRT_URL
ARG VIRTUAL_ENV
ARG BUILD_DEPS="librdkafka gcc linux-headers libc-dev librdkafka-dev"
USER root
WORKDIR /
RUN if [ -z "${CUSTOM_CRT_URL}" ] ; then echo "No custom cert needed"; else \
       wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
       && update-ca-certificates \
    ; fi \
    && apk add --no-cache $BUILD_DEPS
COPY . /app
RUN cd /app \
    && pip install build \
    && python -m build \
    && python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -r /app/requirements.txt \
    && pip install /app/dist/*.whl


################## Stage 1
FROM ${RUN_IMAGE} as runner
ARG CUSTOM_CRT_URL
ARG VIRTUAL_ENV
ARG RUN_USER=guest
ARG RUN_DEPS="shadow librdkafka curl git bash"
ENV TZ=UTC
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PS1="\W \$ "
USER root
COPY --from=builder /app/docker-entrypoint.sh /docker-entrypoint.sh
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
RUN if [ -z "${CUSTOM_CRT_URL}" ] ; then echo "No custom cert needed"; else \
       mkdir -p /usr/local/share/ca-certificates \
       && wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
       && cat /usr/local/share/ca-certificates/customcert.crt >> /etc/ssl/certs/ca-certificates.crt \
    ; fi \
    && apk add --no-cache $RUN_DEPS \
    && ln -s $VIRTUAL_ENV/lib/python3.9/site-packages/jaws_scripts /scripts \
    && chmod +x /scripts/client/*.py \
    && chmod +x /scripts/broker/*.py \
    && chmod +x /scripts/registry/*.py \
    && chown -R ${RUN_USER}:0 ${VIRTUAL_ENV} \
    && chmod -R g+rw ${VIRTUAL_ENV} \
    && usermod -d /tmp guest
USER ${RUN_USER}
WORKDIR /scripts
ENTRYPOINT ["/docker-entrypoint.sh"]