.PHONY: all plot run_ext

CXX = clang++-12

CXXFLAGS = -g3 -Wall -Wextra -fsanitize=address -std=c++2a
LDFLAGS = -fsanitize=address

# speed
#CXXFLAGS = -Wall -Wextra -O3 -std=c++2a

PROGS = reliability reliability_external

all: $(PROGS)

main.o: main.cpp rmodel.h em_model.h

reliability_external.o: reliability_external.cpp rmodel.h em_model.h

reliability: main.o
	$(CXX) -o $@ $(LDFLAGS) $^

reliability_external: reliability_external.o
	$(CXX) -o $@ $(LDFLAGS) $^

plot: $(PROGS)
	./reliability < constant-temperature.log > time-R.csv
	python3 plot-both.py

run: $(PROGS)
	./reliability < constant-temperature.log

run_ext: $(PROGS)
	./reliability_external 1 constant-temperature.log states.txt rvalues.txt

clean:
	rm -f $(PROGS) *.o
