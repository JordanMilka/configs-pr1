run:
	python3 -m src.main

test:
	python3 -m unittest discover -s tests -t . -v

.PHONY: run test
