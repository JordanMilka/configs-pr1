run:
	python3 -m src.main

run-script:
	python3 -m src.main --vfs data/vfs.zip \
		--script scripts/emulator/stage2_demo.txt

test:
	python3 -m unittest discover -s tests -t . -v

.PHONY: run run-script test
