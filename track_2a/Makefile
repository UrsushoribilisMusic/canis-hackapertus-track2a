.PHONY: run run-model test probe-model

# Starts the prototype in Docker from a clean checkout.
run:
	docker build -t canis-hackapertus-track2a .
	docker run --rm -p 8080:8080 canis-hackapertus-track2a

run-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2a-model .
	docker run --rm -p 8080:8080 -e HF_TOKEN -e CANIS_ENABLE_MODEL=1 -e CANIS_MAX_NEW_TOKENS=$${CANIS_MAX_NEW_TOKENS:-32} -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2a-model uvicorn backend.app:app --host 0.0.0.0 --port 8080 --app-dir src

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

probe-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2a-model .
	docker run --rm -e HF_TOKEN -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2a-model
