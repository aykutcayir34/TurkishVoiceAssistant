FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (ses işleme için ffmpeg/libsndfile gerçek backend'lerde gerekir)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# Varsayılan: hafif çekirdek kurulum (mock backend'ler, CPU). Gerçek modeller için
# build-arg ile extras seçilebilir: --build-arg EXTRAS="[all]"
ARG EXTRAS=""
RUN pip install --no-cache-dir -e ".${EXTRAS}"

COPY clients ./clients
COPY scripts ./scripts
COPY data ./data

EXPOSE 8080

CMD ["python", "-m", "sohbet"]
