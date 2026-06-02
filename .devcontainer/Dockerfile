FROM ghcr.io/astral-sh/uv:python3.13-bookworm

ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
ARG WORKSPACE_DIR=/workspaces/trainpit

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        pkg-config \
        sudo \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${WORKSPACE_DIR}

ENV UV_PROJECT_ENVIRONMENT=/workspaces/.venv \
    UV_CACHE_DIR=/home/${USERNAME}/.cache/uv \
    PATH=/workspaces/.venv/bin:${PATH}
