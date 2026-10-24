.PHONY: install data run test clean

install:
	python -m pip install -r requirements.txt

data:            ## download (cached) + clean + validate -> data/processed/
	python scripts/build_dataset.py

run:
	streamlit run app.py

test:
	python -m pytest -q tests

clean:
	rm -rf data/raw data/processed
