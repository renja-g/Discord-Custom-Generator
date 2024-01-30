
FROM python:3.12.1-alpine3.19 as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Install git, gcc and other necessary build tools (git is needed for pip to install from git repos)
RUN apk add --no-cache git gcc musl-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

COPY . .

CMD [ "python", "./main.py" ]
