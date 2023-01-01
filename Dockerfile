FROM python:3.11-alpine

RUN addgroup -S life360 && adduser -S life360 -G life360

USER life360

WORKDIR /app

# Prevents Python from generating pyc files to reduce image size
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1
# Install location of upgraded pip
ENV PATH /home/life360/.local/bin:$PATH

COPY requirements.txt     /app/

RUN pip install --no-cache-dir --disable-pip-version-check --upgrade pip
RUN pip install --no-cache-dir -r ./requirements.txt

COPY *.py                 /app/
COPY template.config.toml /app/

ENTRYPOINT python main.py
