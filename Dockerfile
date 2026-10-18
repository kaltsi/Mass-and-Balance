FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git python3 python3-jinja2 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY generate_sheet.py generate_index.py ./
COPY src/ src/
COPY specs/ specs/

ENTRYPOINT ["python3", "generate_sheet.py", "src/template.html.j2"]
