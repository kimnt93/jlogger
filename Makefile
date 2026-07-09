PYTHON ?= python
UV ?= uv
TEST_PYTHON ?= $(UV) run python
PYTHON_314T ?= python3.14t
MATURIN ?= $(UV) run --with maturin maturin
PKG := jlogger

.PHONY: help native native-314t native-all develop install test test-314t \
	bench bench-314t check fmt build clean

help:
	@printf '%s\n' \
		'Prebuilt-binary workflow (no Rust needed to *install*):' \
		'  make native       Build abi3 .so (CPython 3.9+) into $(PKG)/ and commit it' \
		'  make native-314t  Build free-threaded 3.14t .so into $(PKG)/ and commit it' \
		'  make native-all   Build both prebuilt .so files into $(PKG)/' \
		'' \
		'Development:' \
		'  make develop      Alias for "make native" (build abi3 .so in place)' \
		'  make install      pip install . (uses the committed .so, no Rust)' \
		'  make test         Run unit tests' \
		'  make test-314t    Run unit tests under python3.14t' \
		'  make bench        Benchmark vs stdlib/python-json-logger/structlog' \
		'  make bench-314t   Same benchmark under free-threaded python3.14t' \
		'  make check        cargo check + Python tests' \
		'  make fmt          Format Rust code' \
		'  make build        Build sdist + wheel into dist/' \
		'  make clean        Remove build artifacts (keeps committed .so)'

# Build the abi3 extension (works on every CPython >= 3.9 for this platform)
# and drop it straight into the package directory so it can be committed.
native:
	$(MATURIN) build --release --features abi3 --out dist
	@whl=$$(ls -t dist/$(PKG)-*-abi3-*.whl | head -n1); \
		echo "extracting _native.abi3.so from $$whl"; \
		unzip -o -j "$$whl" '$(PKG)/_native.abi3.so' -d $(PKG)/ >/dev/null
	@ls -la $(PKG)/_native.abi3.so

# Build the free-threaded 3.14t extension. abi3 does not cover the "t" ABI,
# so this is an interpreter-specific build. Requires python3.14t on PATH.
native-314t:
	$(MATURIN) build --release --no-default-features --interpreter $(PYTHON_314T) --out dist
	@whl=$$(ls -t dist/$(PKG)-*-cp314-cp314t-*.whl | head -n1); \
		echo "extracting 3.14t .so from $$whl"; \
		unzip -o -j "$$whl" '$(PKG)/_native.cpython-314t-*.so' -d $(PKG)/ >/dev/null
	@ls -la $(PKG)/_native.cpython-314t-*.so

native-all: native native-314t

develop: native

install:
	$(PYTHON) -m pip install .

test:
	$(TEST_PYTHON) -m unittest discover -s tests

test-314t:
	$(PYTHON_314T) -m unittest discover -s tests

bench:
	PYTHONPATH=. $(UV) run --with structlog --with python-json-logger \
		python benchmarks/bench.py

bench-314t:
	PYTHONPATH=. $(UV) run --with structlog --with python-json-logger \
		--python 3.14t python benchmarks/bench.py

check:
	cargo check
	$(TEST_PYTHON) -m unittest discover -s tests

fmt:
	cargo fmt

build:
	$(UV) run --with build $(PYTHON) -m build --out dist

clean:
	rm -rf build dist target *.egg-info $(PKG).egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
