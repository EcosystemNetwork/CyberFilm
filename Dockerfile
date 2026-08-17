FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv==0.5.24

COPY pyproject.toml uv.lock ./
COPY src ./src
COPY web ./web
COPY README.md LICENSE NOTICE SECURITY.md ./

RUN uv sync

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "cyberfilm.web"]
