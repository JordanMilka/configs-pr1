samples:
	python3 scripts/make_vfs.py data

run:
	python3 -m src.main

run-script: samples
	python3 -m src.main --vfs data/nested.zip \
		--script scripts/emulator/stage3_all.txt

test:
	python3 -m unittest discover -s tests -t . -v

.PHONY: samples run run-script test
