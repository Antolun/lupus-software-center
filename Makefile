.PHONY: all run package clean

all: run

run:
	python3 main.py

package:
	./build-pisi.sh

clean:
	rm -f *.pisi pisim
