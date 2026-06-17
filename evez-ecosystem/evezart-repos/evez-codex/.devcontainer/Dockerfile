FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
# enable 'universe' because musl-tools & clang live there
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common && \
    add-apt-repository --yes universe

# now install build deps and multi-language tooling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential curl git ca-certificates wget \
    pkg-config clang musl-tools libssl-dev just \
    python3 python3-pip python3-venv \
    openjdk-21-jdk maven gradle \
    docker.io && \
    rm -rf /var/lib/apt/lists/*

# Ubuntu 24.04 ships with user 'ubuntu' already created with UID 1000.
USER ubuntu

# install Rust + musl target as dev user
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal && \
    ~/.cargo/bin/rustup target add aarch64-unknown-linux-musl && \
    ~/.cargo/bin/rustup component add clippy rustfmt rust-analyzer

# Install Node.js (LTS) and pnpm
RUN curl -fsSL https://fnm.vercel.app/install | bash && \
    . ~/.bashrc && \
    fnm install 22 && \
    fnm default 22 && \
    npm install -g pnpm typescript ts-node

# Install Go
RUN wget -q https://go.dev/dl/go1.22.0.linux-arm64.tar.gz && \
    tar -C ~ -xzf go1.22.0.linux-arm64.tar.gz && \
    rm go1.22.0.linux-arm64.tar.gz

# Install canonical hashing libraries
# Python: rfc8785
RUN python3 -m pip install --user rfc8785

# Node: json-canonicalize (will be installed in workspace)
# Go: webpki/jcs (will be installed via go get in workspace)
# Rust: serde_jcs (will be added to Cargo workspace)

ENV PATH="/home/ubuntu/.cargo/bin:/home/ubuntu/go/bin:/home/ubuntu/.local/bin:${PATH}"
ENV GOPATH="/home/ubuntu/go"
ENV GOROOT="/home/ubuntu/go"
ENV PATH="${GOPATH}/bin:${GOROOT}/bin:${PATH}"

WORKDIR /workspace
