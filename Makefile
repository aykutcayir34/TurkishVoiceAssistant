.PHONY: install install-all dev test lint ingest up up-gpu down

install:            ## Hafif çekirdek kurulum (mock backend'ler, CPU)
	pip install -e ".[dev]"

install-all:        ## Tüm gerçek model bağımlılıkları (GPU önerilir)
	pip install -e ".[all,dev]"

dev:                ## Mock backend'lerle geliştirme sunucusu
	python scripts/dev_server.py

test:               ## Tüm mock testleri (GPU'suz, deterministik)
	PYTHONPATH=src pytest tests/unit tests/integration tests/e2e -q

lint:
	ruff check src tests
	ruff format --check src tests

ingest:             ## Bilgi tabanını doldur: make ingest DIR=data/docs
	python scripts/ingest.py $(or $(DIR),data/docs)

up:                 ## Docker: qdrant + app (CPU profili)
	docker compose --profile cpu up --build

up-gpu:             ## Docker: qdrant + app + vllm (GPU profili)
	docker compose --profile gpu up --build

down:
	docker compose down
