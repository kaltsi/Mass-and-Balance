FROM python:3.12-alpine

WORKDIR /app

COPY pyproject.toml README ./
COPY parse_template.py template.html.j2 ./
COPY specs/ specs/

RUN pip install --no-cache-dir jinja2

# docker run --rm -v "$PWD/out:/app/out" mass-and-balance specs/oh-kas.json out
ENTRYPOINT ["python", "parse_template.py", "template.html.j2"]
