.PHONY: test eval run-web run-python docker-up lint

test:
	python3 -m unittest discover -s tests -p "test_*.py" -v

eval:
	python3 eval/run_all_evals.py

run:
	npm run dev

run-python:
	uvicorn app.api:app --host 0.0.0.0 --port 8000 & streamlit run app/ui.py --server.port 8501

docker-up:
	docker compose up --build

lint:
	npm run lint
