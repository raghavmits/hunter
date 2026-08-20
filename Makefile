.PHONY: dev

dev: ## Run migrations, then backend + frontend dev servers together (issue #27)
	@./scripts/dev.sh
