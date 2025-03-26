# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# Variables
SPEC_FILE := acp-spec/openapi.json
OUTPUT_DIR := src/agent_workflow_server/generated
OUTPUT_DIR_TMP := src/agent_workflow_server/tmp

PACKAGE_NAME := agent_workflow_server.generated
GENERATOR_IMAGE := openapitools/openapi-generator-cli:latest
ADDITIONAL_PROPERTIES := packageName=$(PACKAGE_NAME)

.PHONY: clean validate-spec update-spec generate-api run docker-build-dev test format lint lint-fix

# Ensure output directory exists
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)


# Clean generated files
clean:
	rm -rf $(OUTPUT_DIR)

validate-spec:
	docker run --rm -v $(PWD):/local $(GENERATOR_IMAGE) validate -i /local/$(SPEC_FILE)

# Update spec (latest commit from submodule)
update-spec:
	git submodule update --remote

# Generate api (models and routes template)
generate-api: clean update-spec
	docker run --rm \
		-v $(PWD):/local \
		$(GENERATOR_IMAGE) generate \
		-i /local/$(SPEC_FILE) \
		-t /local/templates \
		-g python-fastapi \
		-o /local/$(OUTPUT_DIR_TMP) \
		--additional-properties=$(ADDITIONAL_PROPERTIES)
	mkdir -p $(OUTPUT_DIR)/models
	mkdir -p $(OUTPUT_DIR)/apis
	mv $(OUTPUT_DIR_TMP)/$(OUTPUT_DIR)/models $(OUTPUT_DIR)
	mv $(OUTPUT_DIR_TMP)/$(OUTPUT_DIR)/apis $(OUTPUT_DIR)
	rm -rf $(OUTPUT_DIR_TMP)

# Install dependecies and run server
run:
	poetry install
	poetry run server

test:
	poetry run pytest

format:
	poetry run ruff format .

lint:
	poetry run ruff check .

lint-fix:
	poetry run ruff check . --fix

docker-build-dev: ## Build the docker image.
	docker buildx bake workflowserver-dev --load
