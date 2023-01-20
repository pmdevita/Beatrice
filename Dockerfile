FROM python:3.10-alpine as builder
WORKDIR /usr/src/app
RUN apk add libuv libuv-dev libsodium libsodium-dev
RUN pip install virtualenv && virtualenv /app && /app/bin/pip install PyNaCL uvloop cchardet numpy
RUN apk add gcc musl-dev make g++ git
RUN pip install poetry --no-cache-dir
ENV SODIUM_INSTALL=system
COPY . .
RUN poetry build
RUN /app/bin/pip install dist/`ls dist | grep .whl`[mysql,uvloop,speed,audio] --no-cache-dir


FROM python:3.10-alpine
COPY --from=builder /app /app
RUN apk add blas opusfile  # needed for audio
RUN apk add libuv libsodium
WORKDIR /config
CMD ["/app/bin/crescendbot"]
