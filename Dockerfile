FROM python:slim

RUN apt update && \
    apt install -y ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

ENTRYPOINT [ "python3", "-u", "-m", "src.backend.ani_gamer_next" ]
