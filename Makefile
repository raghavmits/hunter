.PHONY: dev backend frontend

dev:
	@trap 'kill 0' SIGINT; \
	uv run uvicorn app.main:app --reload & \
	cd frontend && npm run dev

backend:
	uv run uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev
