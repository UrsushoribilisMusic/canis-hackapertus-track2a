.PHONY: run run-model test probe-model

PORT ?= 8080
CONTAINER_NAME ?= canis-track2b
OPEN ?= 0
URL := http://127.0.0.1:$(PORT)/

define announce_and_maybe_open
	@echo "Canis will be available at $(URL)"
endef

define run_and_maybe_open
	@if [ "$(OPEN)" = "1" ]; then \
		$(1) & \
		run_pid=$$!; \
		for i in $$(seq 1 60); do \
			if ! kill -0 $$run_pid >/dev/null 2>&1; then \
				wait $$run_pid; \
				exit $$?; \
			fi; \
			if curl -fsS "$(URL)api/health" >/dev/null 2>&1; then \
				command -v open >/dev/null 2>&1 && open "$(URL)" || true; \
				break; \
			fi; \
			sleep 1; \
		done; \
		wait $$run_pid; \
	else \
		$(1); \
	fi
endef

# Starts the prototype in Docker from a clean checkout.
run:
	docker build -t canis-hackapertus-track2b .
	$(call announce_and_maybe_open)
	$(call run_and_maybe_open,docker run --rm --name $(CONTAINER_NAME) -p $(PORT):8080 canis-hackapertus-track2b)

run-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2b-model .
	$(call announce_and_maybe_open)
	$(call run_and_maybe_open,docker run --rm --name $(CONTAINER_NAME) -p $(PORT):8080 -e HF_TOKEN -e CANIS_ENABLE_MODEL=1 -e CANIS_MAX_NEW_TOKENS=$${CANIS_MAX_NEW_TOKENS:-32} -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2b-model uvicorn backend.app:app --host 0.0.0.0 --port 8080 --app-dir src)

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

probe-model:
	docker build -f Dockerfile.model -t canis-hackapertus-track2b-model .
	docker run --rm -e HF_TOKEN -e CANIS_MODEL_ID=$${CANIS_MODEL_ID:-swiss-ai/Apertus-v1.5-8B} -v "$${HOME}/.cache/huggingface:/root/.cache/huggingface" canis-hackapertus-track2b-model
