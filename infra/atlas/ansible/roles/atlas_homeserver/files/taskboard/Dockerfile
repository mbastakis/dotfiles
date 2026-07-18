ARG TASK_VERSION=3.4.2
ARG TASK_SHA256=d302761fcd1268e4a5a545613a2b68c61abd50c0bcaade3b3e68d728dd02e716

FROM docker.io/library/ubuntu:24.04 AS taskwarrior-build
ARG TASK_VERSION
ARG TASK_SHA256

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/root/.cargo/bin:${PATH}

RUN apt-get -o Acquire::Retries=5 update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        git \
        gzip \
        tar \
        uuid-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --profile minimal --default-toolchain 1.81.0

WORKDIR /usr/src

RUN curl -fsSLO "https://github.com/GothenburgBitFactory/taskwarrior/releases/download/v${TASK_VERSION}/task-${TASK_VERSION}.tar.gz" \
    && printf '%s  task-%s.tar.gz\n' "${TASK_SHA256}" "${TASK_VERSION}" | sha256sum -c - \
    && tar xzf "task-${TASK_VERSION}.tar.gz" \
    && cmake -S "task-${TASK_VERSION}" -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DENABLE_TLS_NATIVE_ROOTS=ON \
    && cmake --build build --parallel "$(nproc)" \
    && cmake --install build \
    && task --version

FROM docker.io/library/ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TASKBOARD_HOST=0.0.0.0
ENV TASKBOARD_PORT=8080
ENV TASKBOARD_CONFIG=/config
ENV TASKBOARD_DATA=/data
ENV TASKRC=/config/taskrc
ENV TASKDATA=/data

RUN apt-get -o Acquire::Retries=5 update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libstdc++6 \
        libuuid1 \
        python3 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app /config /data \
    && chown -R 1000:1000 /app /config /data

COPY --from=taskwarrior-build /usr/local/ /usr/local/
COPY *.py entrypoint.sh /app/
COPY static/ /app/static/

RUN chmod 0755 /app/entrypoint.sh \
    && chown -R 1000:1000 /app

USER 1000:1000
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
