#ifndef __RELIABILITYAWARE_H
#define __RELIABILITYAWARE_H
#include <vector>
#include "mappingpolicy.h"
#include "migrationpolicy.h"
#include "performance_counters.h"

class ReliabilityAware : public MappingPolicy, public MigrationPolicy {
public:
	ReliabilityAware(const PerformanceCounters *performanceCounters, int coreRows, int coreColumns, float rValueThreshold);
	virtual std::vector<int> map(String taskName, int taskCoreRequirement, const std::vector<bool> &availableCores,const std::vector<bool> &activeCores);
	virtual std::vector<migration> migrate(SubsecondTime time, const std::vector<int> &taskIds, const std::vector<bool> &activeCores);
private:
	const PerformanceCounters *performanceCounters;
	unsigned int coreRows;
	unsigned int coreColumns;
	float rValueThreshold;
	int getMostReliableCore(const std::vector<bool> &availableCores);
	void logRValues(const std::vector<bool> &availableCores);
};

#endif