FROM python:3.10-alpine as builder
WORKDIR /usr/src/app
RUN apk add libuv libuv-dev libsodium libsodium-dev
RUN apk add gcc musl-dev make g++ git
ENV SODIUM_INSTALL=system
RUN pip install virtualenv && virtualenv /app && /app/bin/pip install PyNaCL==1.4.0 uvloop==0.16.0 numpy cchardet
RUN pip install poetry --no-cache-dir
COPY . .
RUN poetry build
RUN /app/bin/pip install dist/`ls dist | grep .whl`[mysql,uvloop,speed,audio] --no-cache-dir


FROM python:3.10-alpine
RUN apk add bash
RUN apk add blas opusfile ffmpeg libsodium # needed for audio
RUN apk add libuv
COPY --from=builder /app /app
WORKDIR /config
CMD ["/app/bin/beatrice"]
