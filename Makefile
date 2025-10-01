PYVERSION ?= 3.10.13
PIPVERSION ?= 2023.11.15

DOCKER = docker
DOCKER-COMPOSE = docker-compose
DOCKER_PLATFORM := linux/amd64

PROJECT_NAME := news_summarizer
LLM_IMAGE := $(PROJECT_NAME)-llm:latest
EMBEDER_IMAGE := $(PROJECT_NAME)-embeder:latest
DB_IMAGE := $(PROJECT_NAME)-db:latest
API_GATEWAY_IMAGE := $(PROJECT_NAME)-api_gateway:latest
LLM_DOCKERFILE := ./deployment/dockerfiles/llm.Dockerfile
EMBEDER_DOCKERFILE := ./deployment/dockerfiles/embeder.Dockerfile
DB_DOCKERFILE := ./deployment/dockerfiles/db.Dockerfile
API_GATEWAY_DOCKERFILE := ./deployment/dockerfiles/api_gateway.Dockerfile

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Availiable commandsfor work with docker:"
	@echo "  make docker-build-image-llm    - Build LLM service image"
	@echo "  make docker-build-image-embeder  - Build embeder image"
	@echo "  make docker-build-image-db-service  - Build Vector DB service image"
	@echo "  make docker-build-image-api-gateway  - Build API gateway image"
	@echo "  make build-all                         - Build all images"
	@echo "  make clean                             - Clean all images"
	@echo "  make list-images                       - Show builded images"


.PHONY: env
define ENV_SAMPLE
# переменная окружения "development" | "production"
ENVIRONMENT="development"

# индекс GPU, на которую усадим модель
GPU_INDEX=0
endef

export ENV_SAMPLE
env:
	$(call _info, $(SEP))
	$(call _info,"Try make .env")
	$(call _info, $(SEP))
	echo "$$ENV_SAMPLE" > .env;

.PHONY: shell
shell:
	pipenv shell

.PHONY: install-deps
install-deps:
	pipenv install --categories="packages dev-packages api inference-server"

.PHONY: pre-commit-install
pre-commit-install:
	pipenv run pre-commit install

.PHONY: create-requirements-txt-api-gateway
create-requirements-txt-api-gateway:
	pipenv requirements --categories="packages" > src/services/api_gateway/requirements.txt

.PHONY: create-requirements-txt-llm
create-requirements-txt-llm:
	pipenv requirements --categories="packages llm" > src/services/llm/requirements.txt

.PHONY: create-requirements-txt-embeder
create-requirements-txt-embeder:
	pipenv requirements --categories="packages embeder" > src/services/embeder/requirements.txt

.PHONY: create-requirements-txt-db-service
create-requirements-txt-db-service:
	pipenv requirements --categories="packages db" > src/services/db/requirements.txt

.PHONY: create-requirements-txt-dev
create-requirements-txt-dev:
	pipenv requirements --categories="dev-packages" > requirements.txt

.PHONY: lint-check
lint-check:
	pipenv run ruff check src

.PHONY: format-check
format-check:
	pipenv run ruff format --check src

.PHONY: type-check
type-check:
	pipenv run pyright src

.PHONY: tests
tests:
	pipenv run pytest tests

.PHONY: lint-fix
lint-fix:
	pipenv run ruff --fix src && pipenv run ruff format src

.PHONY: docker-build-image-llm
docker-build-image-llm: create-requirements-txt-llm
	@echo "Build LLM service image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(LLM_IMAGE) \
		-f $(LLM_DOCKERFILE) \
		.
	@echo "LLM service image builded: $(LLM_IMAGE)"

.PHONY: docker-build-image-embeder
docker-build-image-embeder: 
	@echo "Build Triton client image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(EMBEDER_IMAGE) \
		-f $(EMBEDER_DOCKERFILE) \
		.
	@echo "Triton client image builded: $(EMBEDER_IMAGE)"

.PHONY: docker-build-image-db-service
docker-build-image-db-service: create-requirements-txt-db-service
	@echo "Build vector_db service image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(DB_IMAGE) \
		-f $(DB_DOCKERFILE) \
		.
	@echo "Vector DB service image built: $(DB_IMAGE)"

.PHONY: docker-build-image-api-gateway
docker-build-image-api-gateway: create-requirements-txt-api-gateway
	@echo "Build api_gateway service image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(API_GATEWAY_IMAGE) \
		-f $(API_GATEWAY_DOCKERFILE) \
		.
	@echo "API gateway image built: $(API_GATEWAY_IMAGE)"

.PHONY: build-all
build-all: docker-build-image-llm docker-build-image-embeder docker-build-image-db-service docker-build-image-api-gateway
	@echo "All builded Docker images"
	@echo "Images:"
	@echo "   - $(LLM_IMAGE)"
	@echo "   - $(EMBEDER_IMAGE)"
	@echo "   - $(DB_IMAGE)"
	@echo "   - $(API_GATEWAY_IMAGE)"

.PHONY: list-images
list-images:
	@echo "Builded images:"
	@$(DOCKER) images | grep $(PROJECT_NAME) || echo "📭 Образы не найдены"

.PHONY: clean
clean:
	@echo "Cleaning Docker images..."
	-$(DOCKER) rmi $(LLM_IMAGE) 2>/dev/null || echo "Образ LLM service не найден"
	-$(DOCKER) rmi $(EMBEDER_IMAGE) 2>/dev/null || echo "Образ Triton client не найден"
	@echo "Cleaning is completing"

.PHONY: run-llm
run-llm: docker-build-image-llm
	@echo "Start LLM service container..."
	$(DOCKER) run --gpus all --memory=6g --shm-size=2g -it --rm -p 8000:8000 $(LLM_IMAGE)

.PHONY: run-embeder
run-embeder: docker-build-image-embeder
	@echo "Start Triton client container..."
	$(DOCKER) run --gpus all -it --rm $(EMBEDER_IMAGE)

.PHONY: run-db-service
run-db-service: docker-build-image-db-service
	@echo "Start Vector DB service container..."
	$(DOCKER) run -it --rm -p 6333:6333 $(DB_IMAGE)

.PHONY: run-api-gateway
run-api-gateway: docker-build-image-api-gateway
	@echo "Start API gateway container..."
	$(DOCKER) run --platform $(DOCKER_PLATFORM) -it --rm -p 8000:8000 $(API_GATEWAY_IMAGE)

.PHONY: run-all
run-all:
	$(DOCKER-COMPOSE) -f deployment/docker_compose/docker-compose.yml up -d

.PHONY: install-deps-on-ci
install-deps-on-ci: create-requirements-txt-dev
	python -m pip --cache-dir ./pip-cache install -r requirements.txt

.PHONY: lint-check-ci
lint-check-ci:
	python -m ruff check src

.PHONY: format-check-ci
format-check-ci:
	python -m ruff format --check src

.PHONY: type-check-ci
type-check-ci:
	python -m pyright src

.PHONY: tests-ci
tests-ci:
	python -m pytest tests