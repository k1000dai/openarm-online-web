# Copyright 2026 Enactic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=1

WORKDIR /runner

RUN apt update \
    && apt install -y -V \
        build-essential \
        ffmpeg \
        git \
        libegl-mesa0 \
        libegl1 \
        libgl1 \
        libgl1-mesa-dri \
        libosmesa6 \
        software-properties-common \
    && add-apt-repository -y ppa:openarm/main \
    && apt update \
    && apt install -y -V libopenarm-can-dev

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/runner/.venv/bin:$PATH"
ENV PYTHONPATH="/runner/src"
RUN uv python install 3.14

RUN git clone --branch miraikan --recurse-submodules --shallow-submodules --depth 1 \
    https://github.com/k1000dai/openarm-online-runner.git /runner

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# MuJoCo renders the browser view offscreen on the GPU via headless
# EGL; the compose service passes /dev/dri through for it. Fall back
# to software rendering with MUJOCO_GL=osmesa in .env.runner on a
# host without a usable GPU.
ENV MUJOCO_GL=egl

# The server is teleoperation only: no job queue to poll, and the
# MuJoCo cell dataflows as defaults (the released openarm-mujoco cell
# scene has the head cameras the browser view streams; the pedestal
# scene doesn't yet). .env.runner can override these.
ENV JOBS_ENABLED=false
ENV DEFAULT_KEYBOARD_TELEOPERATION_DATAFLOW_FILE=/runner/dataflows/teleoperation/keyboard/mujoco/dataflow.yaml
ENV DEFAULT_WEBXR_TELEOPERATION_DATAFLOW_FILE=/runner/dataflows/teleoperation/webxr/mujoco/dataflow.yaml

RUN uv run dora build "${DEFAULT_KEYBOARD_TELEOPERATION_DATAFLOW_FILE}" --uv \
    && uv run dora build "${DEFAULT_WEBXR_TELEOPERATION_DATAFLOW_FILE}" --uv

CMD ["uv", "run", "openarm-online-runner"]
