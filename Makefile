# WireClaw Makefile Wrapper for PlatformIO

# Default environment if not specified
ENV ?= esp32-s3-touch-amoled-1-75

.PHONY: all build flash monitor clean config uploadfs

all: build

build:
	pio run -e $(ENV)

flash:
	pio run -e $(ENV) -t upload

monitor:
	pio run -e $(ENV) -t monitor

# Combined command (equivalent to build, flash, monitor)
run:
	pio run -e $(ENV) -t upload -t monitor

# Upload LittleFS data (useful if you change data/config.json)
uploadfs: config
	pio run -e $(ENV) -t uploadfs

# Generate data/config.json from .env
config:
	python3 scripts/generate_config.py

clean:
	pio run -t clean
