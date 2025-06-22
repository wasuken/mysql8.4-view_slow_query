# monitor/Dockerfile
FROM python:3.13-slim

RUN pip install requests watchdog

COPY monitor.py /app/monitor.py
WORKDIR /app

CMD ["/usr/local/bin/python", "monitor.py"]
