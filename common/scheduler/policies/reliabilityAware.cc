#include "reliabilityAware.h"
#include <iomanip>

using namespace std;

ReliabilityAware::ReliabilityAware(const PerformanceCounters *performanceCounters, int coreRows, int coreColumns, float rValueThreshold)
	: performanceCounters(performanceCounters),
	coreRows(coreRows),
	coreColumns(coreColumns),
	rValueThreshold(rValueThreshold) {
	
}

std::vector<int> ReliabilityAware::map(String taskName, int taskCoreRequirement, const std::vector<bool> &availableCoresRO, const std::vector<bool> &activeCores) {
	std::vector<bool> availableCores(availableCoresRO);
	std::vector<int> cores;
	logRValues(availableCores);
	for (; taskCoreRequirement > 0; taskCoreRequirement--) {
		int mostReliableCore = getMostReliableCore(availableCores);
		if (mostReliableCore == -1) {
			// not enough free cores
			std::vector<int> empty;
			return empty;
		} else {
			cores.push_back(mostReliableCore);
			availableCores.at(mostReliableCore) = false;
		}
	}

	return cores;
}

std::vector<migration> ReliabilityAware::migrate(SubsecondTime time, const std::vector<int> &taskIds, const std::vector<bool> &activeCores) {
	std::vector<migration> migrations;
	std::vector<bool> availableCores(coreRows * coreColumns);
	for (int c = 0; c < coreRows * coreColumns; c++) {
		availableCores.at(c) = taskIds.at(c) == -1;
	}
	for (int c = 0; c < coreRows * coreColumns; c++) {
		if (activeCores.at(c)) {
			float rvalue = performanceCounters->getRvalueOfCore(c);
			if (rvalue < rValueThreshold) {
				cout << "[Scheduler][mostReliableCore-migrate]: core" << c << " unreliable (";
				cout << fixed << setprecision(10) << rvalue << ") -> migrate" << endl;
				logRValues(availableCores);
				int targetCore = getMostReliableCore(availableCores);
				cout << "target core: " << targetCore << endl;
				if (targetCore == -1) {
					cout << "[Scheduler][mostReliableCore-migrate]: no target core found, cannot migrate" << endl;
				} else {
					cout << "[Scheduler][mostReliableCore-migrate]: core found, going to migrate to core " << targetCore << endl;
					migration m;
					m.fromCore = c;
					m.toCore = targetCore;
					m.swap = false;
					migrations.push_back(m);
					availableCores.at(targetCore) = false;
				}
			}
		}
	}

	return migrations;
}

int ReliabilityAware::getMostReliableCore(const std::vector<bool> &availableCores) {
	int mostReliableCore = -1;
    float highestRvalue = 0.3;

    for (int c = 0; c < coreRows * coreColumns; c++) {
        if (availableCores.at(c)) {
			cout << "Core: " << c << endl;
            float rvalue = performanceCounters->getRvalueOfCore(c);
            if ((mostReliableCore == -1) || (rvalue > highestRvalue)) {
                mostReliableCore = c;
                highestRvalue = rvalue;
            }
        }
    }

    return mostReliableCore;
}

void ReliabilityAware::logRValues(const std::vector<bool> &availableCores) {
	cout << "[Scheduler][mostReliableCore-map]: Rvalues of available cores:" << endl;
	for (int y = 0; y < coreRows; y++) {
		for (int x = 0; x < coreColumns; x++) {
			if (x > 0) {
				cout << " ";
			}
			int coreId = y * coreColumns + x;
			if (!availableCores.at(coreId)) {
				cout << " - ";
			} else {
				float temperature = performanceCounters->getRvalueOfCore(coreId);
				cout << fixed << setprecision(10) << temperature;
			}
		}
		cout << endl;
	}
}