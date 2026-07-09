PYTHON ?= python
UV ?= uv
TEST_PYTHON ?= $(UV) run python
MATURIN ?= $(UV) run --with maturin maturin

.PHONY: help develop install test build sdist wheel wheel-abi3 wheel-314t check fmt clean

help:
	@printf '%s\n' \
		'Targets:' \
		'  make develop  Build Rust extension in place for local imports' \
		'  make install   Install the package from source with pip' \
		'  make test      Run unit tests' \
		'  make check     Run Rust checks and Python tests' \
		'  make fmt       Format Rust code' \
		'  make build     Build wheel and sdist into dist/' \
		'  make wheel-abi3 Build an abi3 wheel for regular CPython 3.9+' \
		'  make wheel-314t Build a CPython 3.14t free-threaded wheel' \
		'  make clean     Remove build artifacts'

develop:
	$(MATURIN) develop --uv --skip-install

install:
	$(PYTHON) -m pip install .

test:
	$(TEST_PYTHON) -m unittest discover -s tests

check:
	cargo check
	$(TEST_PYTHON) -m unittest discover -s tests

fmt:
	cargo fmt

build:
	$(MATURIN) build --release --sdist --out dist

sdist:
	$(MATURIN) sdist --out dist

wheel:
	$(MATURIN) build --release --out dist

wheel-abi3:
	$(MATURIN) build --release --features abi3 --out dist

wheel-314t:
	$(MATURIN) build --release --no-default-features --interpreter python3.14t --out dist

clean:
	rm -rf build dist target *.egg-info jlogger.egg-info
	rm -f jlogger/*.so
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
