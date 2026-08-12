# Download PARSEC 2.1 through the Figshare API. The institutional download
# endpoint presents an interactive WAF challenge to command-line tools.
PARSEC_2.1_CORE_URL=https://api.figshare.com/v2/file/download/45183391
PARSEC_2.1_SIMSMALL_URL=https://api.figshare.com/v2/file/download/45183310

PARSEC_MAKEFILE_DIR:=$(dir $(realpath $(lastword $(MAKEFILE_LIST))))
ifeq ($(strip $(BENCHMARKS_ROOT)),)
BENCHMARKS_ROOT:=$(realpath $(PARSEC_MAKEFILE_DIR)/..)
endif
ifeq ($(strip $(SNIPER_ROOT)),)
SNIPER_ROOT:=$(realpath $(BENCHMARKS_ROOT)/..)
endif
ifeq ($(strip $(GRAPHITE_ROOT)),)
GRAPHITE_ROOT:=$(SNIPER_ROOT)
endif
export BENCHMARKS_ROOT SNIPER_ROOT GRAPHITE_ROOT

PARSEC_DIR=parsec-2.1
PARSEC_OVERLAY_DIR=sniper-overlay/parsec-2.1
PARSEC_CORE_ARCHIVE=$(PARSEC_DIR)/.parsec-core.tar.gz
PARSEC_SIM_ARCHIVE=$(PARSEC_DIR)/.parsec-sim.tar.gz
PARSEC_OVERLAY_FILES=$(shell find $(PARSEC_OVERLAY_DIR) -type f)
HOOKS_DIR=$(BENCHMARKS_ROOT)/tools/hooks

.PHONY: all parsec-core parsec-input-sim parsec-input-native \
	parsec-dependencies parsec-build clean

all: parsec-build

parsec-core: $(PARSEC_DIR)/.sniper_overlay

$(PARSEC_DIR)/.parsec_source:
	mkdir -p $(PARSEC_DIR)
	wget -O $(PARSEC_CORE_ARCHIVE) $(PARSEC_2.1_CORE_URL)
	tar tzf $(PARSEC_CORE_ARCHIVE) > /dev/null
	tar xzf $(PARSEC_CORE_ARCHIVE)
	rm -f $(PARSEC_CORE_ARCHIVE)
	patch -p1 -d$(PARSEC_DIR) < patches/bugfixes/parsec-ocreat.patch
	patch -p1 -d$(PARSEC_DIR) < patches/bugfixes/ferret-deadlock.patch
	patch -p0 -d$(PARSEC_DIR)/pkgs/apps/blackscholes/src < patches/bugfixes/blackscholes.c.patch
	patch -p0 -d$(PARSEC_DIR)/pkgs/apps/blackscholes/src < patches/bugfixes/blackscholes.tbb.cpp.patch
	patch -p1 -d$(PARSEC_DIR) < patches/bugfixes/streamcluster_barrier.patch
	patch -p1 -d$(PARSEC_DIR) < patches/ssl-asm.patch
	patch -p1 -d$(PARSEC_DIR) < patches/raytrace-unistd-gcc-fix.patch
	patch -p3 -d$(PARSEC_DIR) < patches/raytrace-Xext-fix.patch
	patch -p1 -d$(PARSEC_DIR) < patches/heartbeat.patch
	patches/fixPODSyntax.sh
	touch $(PARSEC_DIR)/.parsec_source

$(PARSEC_DIR)/.sniper_overlay: $(PARSEC_DIR)/.parsec_source $(PARSEC_OVERLAY_FILES)
	cp -a $(PARSEC_OVERLAY_DIR)/. $(PARSEC_DIR)/
	touch $(PARSEC_DIR)/.sniper_overlay

parsec-input-sim: parsec-core $(PARSEC_DIR)/pkgs/apps/blackscholes/inputs/input_simsmall.tar

$(PARSEC_DIR)/pkgs/apps/blackscholes/inputs/input_simsmall.tar: | parsec-core
	wget -O $(PARSEC_SIM_ARCHIVE) $(PARSEC_2.1_SIMSMALL_URL)
	tar tzf $(PARSEC_SIM_ARCHIVE) > /dev/null
	tar xzf $(PARSEC_SIM_ARCHIVE)
	rm -f $(PARSEC_SIM_ARCHIVE)

parsec-input-native: $(PARSEC_DIR)/pkgs/apps/blackscholes/inputs/input_native.tar

$(PARSEC_DIR)/pkgs/apps/blackscholes/inputs/input_native.tar:
	echo "native inputs are not available"; false

parsec-dependencies:
	./checkdependencies.py

parsec-build: parsec-dependencies parsec-core parsec-input-sim
	$(MAKE) -C $(HOOKS_DIR)
	cd $(PARSEC_DIR); ./bin/parsecmgmt -a build -p bench -c gcc-sniper
	cd $(PARSEC_DIR); ./bin/parsecmgmt -a clean -c gcc-sniper

clean:
	$(MAKE) -C $(HOOKS_DIR) clean
	cd $(PARSEC_DIR); ./bin/parsecmgmt -a uninstall -p all -c gcc-sniper
