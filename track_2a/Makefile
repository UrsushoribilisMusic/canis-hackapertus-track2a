.PHONY: run test probe-model

# Starts the prototype in Docker from a clean checkout.
run:
	docker build -t canis-hackapertus-track2a .
	docker run --rm -p 8080:8080 canis-hackapertus-track2a

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

probe-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2a-model .
	docker run --rm -e HF_TOKEN -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2a-model
