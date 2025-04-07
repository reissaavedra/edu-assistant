FROM python:3.10-slim

ENV LANG=C.UTF-8 \
    # python:
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/edu-assistant:$PYTHONPATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry
    POETRY_VERSION=1.8.3

WORKDIR /edu-assistant

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl ffmpeg && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* && \
    # Install poetry
    pip install "poetry==$POETRY_VERSION"

# Install oh-my-zsh

ARG oh_my_zsh=false
RUN if ${oh_my_zsh}; \
    then sh -c "$(curl -L https://github.com/deluan/zsh-in-docker/releases/download/v1.1.5/zsh-in-docker.sh)" -- \
    -p git -p https://github.com/zsh-users/zsh-autosuggestions -t robbyrussell ; \
    else echo "Skipping oh-my-zsh installation" ; \
    fi
# Copy project dependency files to image
COPY pyproject.toml ./

COPY Makefile ./Makefile

ARG build=build
RUN poetry config virtualenvs.create false && \
    make ${build}

COPY . .