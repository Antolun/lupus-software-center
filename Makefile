.PHONY: all build run package clean

all: build

build:
	cargo build --release

run:
	cargo run

package: build
	./build-luppo.sh

clean:
	cargo clean
