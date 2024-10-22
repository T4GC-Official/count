# Set default variables

.PHONY: build push

# Build Docker image, automatically determining build context
build:
	@echo "Building Docker image..."
	$(eval CONTEXT := $(shell dirname $(DOCKERFILE)))
	docker build -f $(DOCKERFILE) -t $(IMAGE):$(TAG) $(CONTEXT)

# Push Docker image to the repository
push:
	@echo "Pushing image to repository..."
	docker push $(IMAGE):$(TAG)

