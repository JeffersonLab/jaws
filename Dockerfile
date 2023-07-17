ARG BASE_IMAGE=slominskir/jaws-base:4.1.1
ARG BUILD_IMAGE=$BASE_IMAGE
ARG RUN_IMAGE=$BASE_IMAGE
ARG BUILD_VIRTUAL_ENV=/opt/venv_dev
ARG RUN_VIRTUAL_ENV=/opt/venv

################## Stage 0
FROM ${BUILD_IMAGE} as builder
ARG CUSTOM_CRT_URL
ARG BUILD_VIRTUAL_ENV
ARG RUN_VIRTUAL_ENV
USER root
WORKDIR /
RUN if [ -z "${CUSTOM_CRT_URL}" ] ; then echo "No custom cert needed"; else \
       wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
       && update-ca-certificates \
    ; fi
COPY . /app
ENV PATH="$BUILD_VIRTUAL_ENV/bin:$PATH"
RUN cd /app \
    && cp -r $RUN_VIRTUAL_ENV $BUILD_VIRTUAL_ENV \
    && python -m pip install ".[dev]" \
    && pylint src/jaws_scripts \
    && python -m build \
    && python -m sphinx.cmd.build -b html docsrc/source build/docs


################## Stage 1
FROM ${RUN_IMAGE} as runnerbase
ARG CUSTOM_CRT_URL
ARG RUN_VIRTUAL_ENV
ARG RUN_USER=guest
ENV TZ=UTC
USER root
COPY --from=builder /app/docker-entrypoint.sh /docker-entrypoint.sh
COPY --from=builder /app/dist/*.whl /tmp
RUN if [ -z "${CUSTOM_CRT_URL}" ] ; then echo "No custom cert needed"; else \
       mkdir -p /usr/local/share/ca-certificates \
       && wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
       && cat /usr/local/share/ca-certificates/customcert.crt >> /etc/ssl/certs/ca-certificates.crt \
    ; fi \
    && pip install /tmp/*.whl \
    && ln -s $RUN_VIRTUAL_ENV/lib/python3.9/site-packages/jaws_scripts /scripts \
    && chmod +x /scripts/client/*.py \
    && chmod +x /scripts/broker/*.py \
    && chmod +x /scripts/registry/*.py \
    && chown -R ${RUN_USER}:0 ${RUN_VIRTUAL_ENV} \
    && chmod -R g+rw ${RUN_VIRTUAL_ENV}
USER ${RUN_USER}
WORKDIR /scripts
ENTRYPOINT ["/docker-entrypoint.sh"]

################## Stage 2
FROM runnerbase as tester
ARG BUILD_VIRTUAL_ENV
COPY --from=builder /app /app
COPY --from=builder $BUILD_VIRTUAL_ENV $BUILD_VIRTUAL_ENV
ENV PATH="$BUILD_VIRTUAL_ENV/bin:$PATH"

################## Stage 3 (default)
FROM runnerbase as runner