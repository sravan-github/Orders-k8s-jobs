FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -r -u 10001 appuser
USER 10001

EXPOSE 8080
# Default = API. Job and CronJob override the command.
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "api:app"]
