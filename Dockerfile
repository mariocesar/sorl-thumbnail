FROM ubuntu:26.04

RUN apt-get update && apt-get install -y \
    imagemagick \
    libgraphicsmagick1-dev \
    libgraphicsmagick++1-dev \
    graphicsmagick \
    libjpeg62 \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Show ImageMagick version
RUN convert --version

# tox runs on uv; uv also provides every Python in the tox envlist
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv python install 3.10 3.11 3.12 3.13 3.14 \
    && uv tool install tox --with tox-uv --with tox-gh-actions
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY . /app/

# Usage: docker compose run --rm test tox -e py312-django52-pil (see docs/contributing.rst)
CMD ["tox"]
