.PHONY: all build run package clean

all: build

build:
	cd src-tauri && cargo build --release

run:
	cd src-tauri && cargo run

package: build
	./build-luppo.sh

clean:
	cd src-tauri && cargo clean
