#include "performance_counters.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <numeric>
#include <iostream>
#include <iomanip>

using namespace std;

PerformanceCounters::PerformanceCounters(const char* output_dir,
        std::string instPowerFileNameParam,
        std::string instTemperatureFileNameParam,
        std::string instCPIStackFileNameParam,
        std::string instRvalueFileNameParam) :
            instPowerFileName(instPowerFileNameParam),
            instTemperatureFileName(instTemperatureFileNameParam),
            instCPIStackFileName(instCPIStackFileNameParam) {

    //gkothar1: fix log file path names
    std::string temp = instPowerFileName;
    instPowerFileName = std::string(output_dir);
    instPowerFileName.append("/");
    instPowerFileName.append(temp);

    temp = instTemperatureFileName;
    instTemperatureFileName = std::string(output_dir);
    instTemperatureFileName.append("/");
    instTemperatureFileName.append(temp);

    temp = instCPIStackFileName;
    instCPIStackFileName = std::string(output_dir);
    instCPIStackFileName.append("/");
    instCPIStackFileName.append(temp);

    instRvalueFileName = std::string(output_dir) + "/" +
        instRvalueFileNameParam;
}

// /** Return a vector of all the values that match the prefix pattern. */
// vector<double> getValues(string filename, string prefix) {
//     ifstream LogFile(filename);
//     string header;
//     string footer;
//     vector<double> v;

//     if (LogFile.good()) {
//         getline(LogFile, header);
//         getline(LogFile, footer);
//     }

//     std::istringstream issHeader(header);
//     std::istringstream issFooter(footer);
//     std::string token;

//     while(getline(issHeader, token, '\t')) {
//         std::string value;
//         getline(issFooter, value, '\t');
//         if (token.find(prefix) == 0) {
//             v.push_back(stod(value));
//         }
//     }

//     return v;
// }

vector<double> getValues(string filename, string prefix) {
    ifstream LogFile(filename);
    string header;
    string footer;
    vector<double> v;

    if (!LogFile.is_open()) {
        cout << "Error: Could not open file " << filename << endl;
        return v;
    }

    // Read the first two lines (header and footer)
    if (LogFile.good()) {
        getline(LogFile, header);
        getline(LogFile, footer);
    }

    // Print the raw header and footer for debugging
    // cout << "Header: " << header << endl;
    // cout << "Footer: " << footer << endl;

    std::istringstream issHeader(header);
    std::istringstream issFooter(footer);
    std::string token;

    // cout << "Processing columns with prefix: " << prefix << endl;

    while (getline(issHeader, token, '\t')) {
        std::string value;
        if (!getline(issFooter, value, '\t')) {
            // cout << "Warning: Mismatch between header and footer columns." << endl;
            break;
        }

        // cout << "Token: " << token << ", Value: " << value << endl;

        if (token.find(prefix) == 0) {
            try {
                double num = stod(value);
                // cout << "Matched: " << token << " -> " << fixed << setprecision(10) << num << endl;
                v.push_back(num);
            } catch (const std::exception &e) {
                cout << "Error converting value to double: " << value << " (" << e.what() << ")" << endl;
            }
        }
    }

    // cout << "Extracted values: ";
    // for (double val : v) {
    //     cout << fixed << setprecision(10) << val << " ";
    // }
    // cout << endl;

    return v;
}

/** Return the value of a component in the instantanious `logfile`.
 * Return -1 if the component is not found and throw an exception if
 * the component is found multiple times.
 */
double getValue(string logfile, string component) {
    vector<double> values = getValues(logfile, component);

    if (values.size() < 1) {
        return -1;
    } else if (values.size() > 1) {
        throw std::runtime_error{"ERROR: Duplicate components found in " + \
            logfile};
    }

    return values[0];
}

/** getPowerOfComponent
    Returns the latest power consumption of a component being tracked using base.cfg. Return -1 if power value not found.
*/
double PerformanceCounters::getPowerOfComponent (string component) const {
    return getValue(instPowerFileName, component);
}

/** getPowerOfCore
 * Return the current power usage of the Core 'coreId' or -1 if no value
 * was found.
 * We don't track core power usage so we calculate it by summing the power
 * usage of all the subcomponents of the core.
 */
double PerformanceCounters::getPowerOfCore(int coreId) const {
    string prefix = "C_" + std::to_string(coreId) + "_";
    vector<double> power_values = getValues(instPowerFileName, prefix);

    if (power_values.size() == 0) {
        return -1;
    }

    return std::accumulate(power_values.begin(), power_values.end(), 0.0);
}

/** getPeakTemperature
 * Returns the latest peak temperature of any component or -1 if no
 * temperature value is found.
*/
double PerformanceCounters::getPeakTemperature () const {
    // The pattern 'C_' will match all components in the logfile.
    vector<double> temperatures = getValues(instTemperatureFileName, "C_");

    if (temperatures.size() == 0) {
        return -1;
    }

    return *std::max_element(temperatures.begin(), temperatures.end());
}


/** getTemperatureOfComponent
    Returns the latest temperature of a component being tracked using base.cfg. Return -1 if power value not found.
*/
double PerformanceCounters::getTemperatureOfComponent (string component) const {
    return getValue(instTemperatureFileName, component);
}

/** getTemperatureOfCore
 * Return the latest temperature of the given core or -1 if no value was
 * found.
 * We don't track the temperature at core level so we calculate it by
 * taking the maximum of all the subcomponents of the core.
 */
double PerformanceCounters::getTemperatureOfCore(int coreId) const {
    string prefix = "C_" + std::to_string(coreId) + "_";
    vector<double> temperatures = getValues(instTemperatureFileName, prefix);

    if (temperatures.size() == 0) {
        return -1;
    }

    return *std::max_element(temperatures.begin(), temperatures.end());
}

/**
 * Get a performance metric for the given core.
 * Available performance metrics can be checked in InstantaneousPerformanceCounters.log
 */
double PerformanceCounters::getCPIStackPartOfCore(int coreId, std::string metric) const {
    ifstream cpiStackLogFile(instCPIStackFileName);
    string line;
    std::istringstream issLine;

    // first find the line in the logfile that contains the desired metric
    bool metricFound = false;
    while (!metricFound) {
        if (cpiStackLogFile.good()) {
            getline(cpiStackLogFile, line);
            issLine.str(line);
            issLine.clear();
            std::string m;
            getline(issLine, m, '\t');
            metricFound = (m == metric);
        } else {
            return -1;
        }
    }
    
    // then split the coreId-th value from this line (first value is metric name, but already consumed above)
    std::string value;
    for (int i = 0; i < coreId + 1; i++) {
        getline(issLine, value, '\t');
        if ((i == 0) && (value == "-")) {
            return 0;
        }
    }

    return stod(value);
}

/**
 * Get the utilization of the given core.
 */
double PerformanceCounters::getUtilizationOfCore(int coreId) const {
    return getCPIStackPartOfCore(coreId, "base") / getCPIOfCore(coreId);
}

/**
 * Get the CPI of the given core.
 */
double PerformanceCounters::getCPIOfCore(int coreId) const {
    return getCPIStackPartOfCore(coreId, "total");
}

/**
 * Get the rel. NUCA part of the CPI stack of the given core.
 */
double PerformanceCounters::getRelNUCACPIOfCore(int coreId) const {
    return getCPIStackPartOfCore(coreId, "mem-nuca") / getCPIOfCore(coreId);
}

/**
 * Get the frequency of the given core.
 */
int PerformanceCounters::getFreqOfCore(int coreId) const {
    if (coreId >= (int)frequencies.size()) {
        return -1;
    } else {
        return frequencies.at(coreId);
    }
}

/**
 * Notify new frequencies
 */
void PerformanceCounters::notifyFreqsOfCores(std::vector<int> newFrequencies) {
    frequencies = newFrequencies;
}

/**
 * Get the frequency of the given core.
 */
double PerformanceCounters::getIPSOfCore(int coreId) const {
    return 1e6 * getFreqOfCore(coreId) / getCPIOfCore(coreId);
}

/** getRvalueOfComponent
    Returns the latest reliability value of the component `component`.
    Return -1 if rvalue value not found.
*/
double PerformanceCounters::getRvalueOfComponent (std::string component) const {
    return getValue(instRvalueFileName, component);
}

/** getRvalueOfCore
 * Return the latest reliability value of the given core or -1 if no value
 * was found.
 * The reliability value of the core is the minimum of the reliability
 * values of its subcomponents.
 */
double PerformanceCounters::getRvalueOfCore(int coreId) const {
    string prefix = "C_" + std::to_string(coreId) + "_";
    cout << "instRvalueFileName: " << instRvalueFileName << ", prefix: " << prefix << endl;

    vector<double> r_values = getValues(instRvalueFileName, prefix);

    // Print extracted values
    cout << "Extracted values: ";
    for (double val : r_values) {
        cout << std::fixed << std::setprecision(10) << val << " ";
    }
    cout << endl;

    // Handle empty vector case
    if (r_values.empty()) {
        cout << "No values found. Returning -1." << endl;
        return -1;
    }

    // Find and print the minimum value
    double min_value = *std::min_element(r_values.begin(), r_values.end());
    cout << "Minimum R-value: " << std::fixed << std::setprecision(10) << min_value << endl;

    return min_value;
}

int PerformanceCounters::getLastBeat(int appId) const {
	std::string target = std::to_string(appId) + ".hb.log";
	std::ifstream appIdHbLogfile(target);
	if (!appIdHbLogfile.is_open()) {
		std::cerr << "[PerformanceCounters] Could not open hb logfile " << target << endl;
		return -1;
	}

	std::string header;
	std::getline(appIdHbLogfile, header);

	std::string line;
	std::string footer;
	while (std::getline(appIdHbLogfile, line)) {
		footer = line;
	}

	if (footer == "") {
		return 0; // No heartbeat data logged yet.
	}

	std::istringstream issHeader(header);
	std::istringstream issFooter(footer);
	std::string token;
	while (std::getline(issHeader, token, '\t')) {
		std::string value;
		std::getline(issFooter, value, '\t');

		if (token == "Timestamp") {
			return std::stoi(value);
		}
	}

	std::cerr << "[PerformanceCounters] Could not find timestamp column in hb file " << target << endl;

  return -1;
}
