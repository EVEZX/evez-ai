# Makefile for OpenClaw hybrid deployment

.PHONY: test kubernetes-up kubernetes-status backup

# 1. Validate configuration (dry-run)
test:
	@echo "Running configuration validation..."
	openclaw config validate || echo "Validation failed"

# 2. Deploy Kubernetes cluster (placeholder)
kubernetes-up:
	@echo "Deploying Kubernetes cluster..."
	# Insert your kubectl/helm deployment commands here

# 3. Show cluster status
kubernetes-status:
	@echo "Fetching Kubernetes status..."
	# Insert kubectl get pods, etc.

# 4. Create backup of current workspace
backup:
	@echo "Creating workspace backup..."
	tar -czf backup.tar.gz -C $(CURDIR) .
