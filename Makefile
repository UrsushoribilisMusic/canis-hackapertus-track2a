.PHONY: run run-model test probe-model

run:
	$(MAKE) -C track_2b run

run-model:
	$(MAKE) -C track_2b run-model

test:
	$(MAKE) -C track_2b test

probe-model:
	$(MAKE) -C track_2b probe-model
