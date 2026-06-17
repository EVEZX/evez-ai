.PHONY: install run dev test clean verify

install:
	python3 -m venv .venv
	.venv/bin/pip install -q -r requirements.txt
	@[ -f .env ] || cp .env.example .env

run:
	source .venv/bin/activate && python run.py

dev:
	source .venv/bin/activate && uvicorn api.app:app --reload --host 0.0.0.0 --port 8420

test:
	source .venv/bin/activate && python -m pytest tests/ -v

verify:
	source .venv/bin/activate && python cli.py verify

clean:
	rm -rf data/tasks.db data/spine.jsonl data/chroma data/drafts

status:
	source .venv/bin/activate && python cli.py health
