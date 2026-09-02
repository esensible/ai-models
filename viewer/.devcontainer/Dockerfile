# Viewer build/deploy devcontainer — Node + Python/uv + Pulumi + AWS CLI.
# Explicit installs (no devcontainer "features"): the feature install path uses apt-key,
# which fails under rootless podman builds ("can't create /tmp/apt.conf…"). Native arm64.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Node 22 — copied from the official image (avoids NodeSource/apt-key under podman).
COPY --from=docker.io/library/node:22-bookworm-slim /usr/local /usr/local

# uv — Python deps + lambda bundling.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip \
      git make curl ca-certificates unzip zip \
    && rm -rf /var/lib/apt/lists/* \
    && corepack enable || true

# AWS CLI v2 (arm64).
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o /tmp/awscli.zip \
    && unzip -q /tmp/awscli.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscli.zip

# Pulumi CLI — install as root, expose globally so the vscode user can run it.
RUN curl -fsSL https://get.pulumi.com | sh \
    && cp /root/.pulumi/bin/* /usr/local/bin/ \
    && pulumi version

USER vscode
