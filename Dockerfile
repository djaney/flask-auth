FROM python:3.7.2-alpine3.9
ARG env=production
RUN mkdir -p /app
WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt && \
    if [ "${env}" = "test" ]; then pip install pytest; fi

EXPOSE 5100

ENTRYPOINT python app.py