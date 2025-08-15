# =======================
# Dockerfile
# =======================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    gcc python3-dev libffi-dev \
    supervisor \
    curl vim lsb-release ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Setup Python virtual environment and install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r /tmp/requirements.txt

# Buat supervisord.conf langsung di Dockerfile
RUN echo "[supervisord]\n\
nodaemon=true\n\
\n\
[program:slemp]\n\
command=/opt/venv/bin/gunicorn app:app --chdir /var/www/panel --bind 0.0.0.0:7777 --worker-class eventlet --workers 1 --timeout 300\n\
autostart=true\n\
autorestart=true" \
> /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 80 3306 7777

# Volume mounts
VOLUME ["/var/www/html", "/var/www/panel"]

# Start supervisord
CMD ["/usr/bin/supervisord", "-n"]
