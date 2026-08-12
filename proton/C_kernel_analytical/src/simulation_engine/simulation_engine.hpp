#ifndef SIMULATION_ENGINE_SIMULATION_ENGINE_HPP_
#define SIMULATION_ENGINE_SIMULATION_ENGINE_HPP_

#include "../types.hpp"
#include <boost/filesystem.hpp>
#include <chrono>
#include <fftw3.h>
#include <iostream>
#include <string.h>
#include <fstream>
#include <boost/tokenizer.hpp>
// #include <filesystem>

class simulation_engine
{

private:

	PRECISION_TYPE	exec_time;				//!< The time required for the analytical simulation
	eigen_triplet_vector_T 	triplet_mat_B;	//!< Matrix B in TRIPLETs format
	string triplet_mat_file;  				//!< The name of the matrix B file to be parsed 
	eigen_triplet_vector_T* triplet_mat; 	//!< A vector of TRIPLETs for matrix B
	
	unsigned int num_nodes;
	PRECISION_TYPE coeff;
	PRECISION_TYPE simulation_time;
	string input_location;
	string config_filename;

	my_VectorXd resulting_stress;

	void dct1d(const my_VectorXd& in, my_VectorXd& out);
	void idct1d(const my_VectorXd& in, my_VectorXd& out);

	void form_analytical_solution(my_VectorXd& lambdas, my_VectorXd& right_side_matrix, my_VectorXd& right_side_matrix2, const unsigned int nx_total, const SpMat_l& B, const my_VectorXd u, const my_VectorXd initial_stress);
	void calc_analytical_solution(my_VectorXd& stress, const my_VectorXd& lambdas, const my_VectorXd& right_side_matrix, const my_VectorXd& right_side_matrix2, const unsigned int nx_total, const PRECISION_TYPE t);

	void analytical(const SpMat_l& B, const my_VectorXd& curden, my_VectorXd& initial_stress, const string& output_location);

	void read_file(const string& filename);
	void tripletParser(eigen_triplet_vector_T* _triplet_mat);
public:

	simulation_engine();
	simulation_engine(const string _config_filename);
	~simulation_engine();

	void analyical_wrapper();

	PRECISION_TYPE get_simulation_time();

	void set_num_nodes(const unsigned int number);
	void set_input_location(const string input_location);
	void set_coeff(PRECISION_TYPE coeff);
};

#endif /* SIMULATION_ENGINE_SIMULATION_ENGINE_HPP_ */