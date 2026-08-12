#define EIGEN_USE_MKL_ALL	// Enables the use of Intel MKL BLAS level 2/3 and Lapack routines, as well as the Intel MKL vector operations

#include "simulation_engine/simulation_engine.hpp"
#include "mkl.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

using namespace std;
using namespace std::chrono;

void Logger(string logMsg)
{

	string filePath = "./output_log.txt";
	ofstream ofs(filePath.c_str(), std::ios_base::out | std::ios_base::app);
	ofs << logMsg;
	ofs.close();
}

void print_tool_configuration(unsigned int threads)
{
	cout << endl;
	cout << "\n-------- Tool configuration ----------" << endl;
	Logger("-------- Tool configuration ----------\n");
#if ENABLE_DOUBLES
	cout << "Precision type: double" << endl;
	Logger("Precision type: double\n");
#else
	cout << "Precision type: float" << endl;
	Logger("Precision type: float\n");
#endif // ENABLE_DOUBLES

	cout << "Threads: " << threads << endl;
	Logger("Threads: " + to_string(threads) + "\n");

	cout << "--------------------------------------" << endl;
	Logger("--------------------------------------\n\n");

}

void print_runtime_results(high_resolution_clock::time_point* timings, PRECISION_TYPE simulation_time)
{
	cout << "\n----------- Runtime results ------------------" << endl;
	Logger("\n----------- Runtime results ------------------\n");
	cout << "Analytical time: " << duration_cast<duration<PRECISION_TYPE>>(timings[1] - timings[0]).count() << "s" << endl;
	Logger("Analytical time: " + to_string(duration_cast<duration<PRECISION_TYPE>>(timings[1] - timings[0]).count()) + "s\n");
	cout << "----------------------------------------------" << endl;
	Logger("----------------------------------------------\n");
}

int main(int argc, char* argv[])
{	
	high_resolution_clock::time_point timings[2];	//used for runtime measurements

#if DEBUG_ANALYTICAL
	cout << "C Kernel - Analytical solution for PROTON tool\n\n";
#endif

	timings[0] = high_resolution_clock::now();

	/* Set the number of threads for OpenMP, Eigen and MKL */
	unsigned int threads = 4;
	Eigen::setNbThreads(threads);
	omp_set_num_threads(threads);
	mkl_set_num_threads(threads);
	mkl_set_num_threads_local(threads);

	/* Print info about the tool configuration */
	// print_tool_configuration(threads);
	
	string config_file;

	if (argc == 2)
		config_file = argv[1]; // "config.cfg"
	else
	{
		cout << "Wrong number of arguments. Configuration file expected." << endl;
		exit(1);
	}

	/* Run the engine of analytical */
	simulation_engine* analytical_sim_engine; 
	analytical_sim_engine = new simulation_engine(config_file); 
	analytical_sim_engine->analyical_wrapper();

	timings[1] = high_resolution_clock::now();

	/* Print the runtime for the analytical method */
	// print_runtime_results(timings, analytical_sim_engine->get_simulation_time());

	return 0;
}
