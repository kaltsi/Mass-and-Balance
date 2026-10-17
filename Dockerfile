FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git python3 python3-jinja2 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY parse_template.py generate_index.py template.html.j2 index.html.j2 ./
COPY specs/ specs/

# docker run --rm -v "$PWD/out:/app/out" mass-and-balance specs/oh-kas.json out
# docker run --rm -v "$PWD/.git:/app/.git" --entrypoint python3 mass-and-balance generate_index.py index.html.j2 specs out
ENTRYPOINT ["python3", "parse_template.py", "template.html.j2"]
