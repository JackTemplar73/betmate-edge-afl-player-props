FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN chmod +x /app/run_hosted_betmate_edge.sh /app/bootstrap_railway_state.sh

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BETMATE_REFRESH_HOST=127.0.0.1 \
    BETMATE_REFRESH_PORT=8765 \
    BETMATE_PUBLIC_HOST=0.0.0.0 \
    BETMATE_STATE_DIR=/data \
    PORT=8000

EXPOSE 8000

CMD ["/app/run_hosted_betmate_edge.sh"]
