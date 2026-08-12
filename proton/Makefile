.PHONY: all analytical check clean

all: check

# The DC solver is distributed by upstream PROTON as a Linux binary. The
# analytical kernel can also be rebuilt from the retained source below.
check:
	@test -x bin/circuit_simulation || { echo "Missing proton/bin/circuit_simulation"; exit 1; }
	@test -x bin/EMtool_analytical || { echo "Missing proton/bin/EMtool_analytical"; exit 1; }

analytical:
	./C_kernel_analytical/build_analytical.sh

clean:
	rm -f bin/EMtool_analytical
