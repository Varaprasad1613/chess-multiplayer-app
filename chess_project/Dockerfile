FROM python:3.12.6
WORKDIR /app
COPY requirements.txt ./
RUN pip3 install --user -r requirements.txt
RUN apt update && apt install -y redis-server supervisor && apt clean
COPY . ./
RUN chmod +x docker_run_server.sh
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/supervisord.conf
EXPOSE 80
ENV PYTHONUNBUFFERED=1
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
