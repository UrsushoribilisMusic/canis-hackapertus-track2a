.PHONY: run run-model test probe-model

PORT ?= 8080
CONTAINER_NAME ?= canis-track2b

# Starts the prototype in Docker from a clean checkout.
run:
	docker build -t canis-hackapertus-track2b .
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):8080 canis-hackapertus-track2b

run-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2b-model .
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):8080 -e HF_TOKEN -e CANIS_ENABLE_MODEL=1 -e CANIS_MAX_NEW_TOKENS=$${CANIS_MAX_NEW_TOKENS:-32} -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2b-model uvicorn backend.app:app --host 0.0.0.0 --port 8080 --app-dir src

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

probe-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2b-model .
	docker run --rm -e HF_TOKEN -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2b-model
