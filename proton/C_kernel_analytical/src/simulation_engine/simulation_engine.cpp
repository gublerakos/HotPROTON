#include "simulation_engine.hpp"

using namespace std::chrono;
using namespace boost;


simulation_engine::simulation_engine(): exec_time(0)
{
}

simulation_engine::~simulation_engine()
{
}

simulation_engine::simulation_engine(const string _config_filename): 
	exec_time(0), config_filename(_config_filename)
{
	read_file(config_filename);
}

void simulation_engine::read_file(const string& filename) {
	ifstream infile(filename);
	string line;

	string input_files;
	int num_nodes = 0;
	PRECISION_TYPE A_coeff = 0.0;
	PRECISION_TYPE sim_time;

	bool INPUT_FLAG, NODES_FLAG, COEFF_FLAG, TIME_FLAG;
	INPUT_FLAG = NODES_FLAG = COEFF_FLAG = TIME_FLAG = false;
	while (getline(infile, line)) {
		istringstream iss(line);
		string keyword;

		if (iss >> keyword) {
			if (keyword == "input_files") {
				iss >> input_files;
				INPUT_FLAG = true;
			}
			else if (keyword == "num_nodes") {
				iss >> num_nodes;
				NODES_FLAG = true;
			}
			else if (keyword == "A_coeff") {
				iss >> A_coeff;
				COEFF_FLAG = true;
			}
			else if (keyword == "simulation_time") {
				iss >> sim_time;
				TIME_FLAG = true;
			}
		}
	}

	if (!INPUT_FLAG)
	{
		cout << filename << " The configuration file does not include the input directory." << endl; 
		exit(1);
	}

	if (!NODES_FLAG)
	{
		cout << "The configuration file does not include the number of nodes." << endl; 
		exit(1);
	}

	if (!COEFF_FLAG)
	{
		cout << "The configuration file does not include the A coefficient." << endl; 
		exit(1);
	}

	if (!TIME_FLAG)
	{
		cout << "The configuration file does not include the target simulation time." << endl; 
		exit(1);
	}

	this->coeff = A_coeff;
	this->num_nodes = num_nodes;
	this->input_location = input_files;
	this->simulation_time = sim_time;

#if DEBUG_ANALYTICAL
	cout << "input_files: " << input_files << endl;
	cout << "num_nodes: " << num_nodes << endl;
	cout << "A_coeff: " << A_coeff << endl;
	cout << "sim_time: " << sim_time << endl;

	cout << "this->input_location: " << this->input_location << endl;
	cout << "this->num_nodes: " << this->num_nodes << endl;
	cout << "this->coeff: " << this->coeff << endl;
	cout << "this->simulation_time: " << this->simulation_time << endl;
#endif
}

void simulation_engine::set_num_nodes(const unsigned int number)
{
	this->num_nodes = number;
}

void simulation_engine::set_input_location(const string input_location)
{
	this->input_location = input_location;
}

void simulation_engine::set_coeff(PRECISION_TYPE coeff)
{
	this->coeff = coeff;
}

PRECISION_TYPE simulation_engine::get_simulation_time()
{
	return this->simulation_time;
}

void simulation_engine::tripletParser(eigen_triplet_vector_T* _triplet_mat)
{

	if (!triplet_mat_file.empty())
	{
		triplet_mat = _triplet_mat;

		ifstream file;
		string buf = "\0";

		string working_file;

		unsigned int line_cnt = 1;
		working_file = triplet_mat_file;

		unsigned int number_nodes = 0;
		file.open(working_file.c_str());
		if (!file.good())
		{
			cout << "Terminating" << endl;
			cout << "The file " << working_file << " was not found.\n";
			cout << "Terminating.\n";
			exit(1);
		}

		while (true)
		{

			/**
			* 	Valid syntax format for power_distr file format: <part>,<second_node>,<element_value>
			*/

			getline(file, buf);

			if (file.eof())
			{
				break;

			}

			typedef tokenizer<char_separator<char> > tokenizer;
			bool foundThirdCap = false;

			char_separator<char> sep(", \t");
			tokenizer tokens(buf, sep);

			tokenizer::iterator tok_iter = tokens.begin();

			if (tok_iter != tokens.end())
			{

				string token_values[4];

				// get the 1st token
				token_values[0] = *tok_iter;


				tok_iter++;

				// get the 2nd token
				if (tok_iter != tokens.end())
				{
					token_values[1] = *tok_iter;

				}
				else
				{
					cout << "Required second value at line "
						<< line_cnt << " of the file " << working_file
						<< ".\n";
					cout << "Terminating.\n";
					exit(1);

				}

				tok_iter++;

				// get the 3th token
				if (tok_iter != tokens.end())
				{
					token_values[2] = *tok_iter;
				}
				else
				{
					cout << "Required third value at line "
						<< line_cnt << " of the file " << working_file
						<< ".\n";
					cout << "Terminating.\n";
					exit(1);

				}

				//if the syntax of the parsed line is valid:
				// 1. extract the information
				// 2. update the triplet vector

				string first_node;
				string second_node;
				string part;

				PRECISION_TYPE element_value;

				first_node = token_values[0];
				second_node = token_values[1];
				element_value = (PRECISION_TYPE)atof((char*)token_values[2].c_str());

				triplet_mat->push_back(eigen_triplet_T(std::stoi(first_node), std::stoi(second_node), element_value));
				if ((unsigned int)(std::stoi(second_node) + 1) > number_nodes)
				{
					number_nodes = line_cnt;
				}

				line_cnt++;
			}

		}
#if DEBUG_ANALYICAL
		cout << "Parsing is done!" << endl;
#endif
		file.close();
	}
	else {
		cout << "Error parsing file "  << triplet_mat_file << endl;
		exit(1);
	}
}

void simulation_engine::analyical_wrapper()
{	

	high_resolution_clock::time_point timings[2];	//used for runtime measurements
	timings[0] = high_resolution_clock::now();

	/* Calculate analytical stress */

	unsigned int nodes_number = this->num_nodes;

	string input_location = this->input_location;

	// Find the position of "output" in the string
	string output_location = input_location;
	size_t pos = output_location.find("input");
	if (pos != std::string::npos) {
		// Replace "output" with "input"
		output_location.replace(pos, 5, "output");
	}

	string input_file_location = input_location + "curden.csv";
	ifstream input_file(input_file_location);
	string line;

	// count the number of lines in the input file
	int num_lines = 0;
	while (std::getline(input_file, line)) {
		num_lines++;
	}
	input_file.close();
	my_VectorXd curden(num_lines);

	unsigned int ports = num_lines;

	// reopen the input file and read the values into my_vector
	input_file.open(input_file_location);
	int i = 0;
	while (getline(input_file, line)) {
		curden(i) = stod(line); // double precision. Maybe going to change this
		i++;
	}
	input_file.close();

#if DEBUG_ANALYTICAL
	cout << "curden size: " << curden.rows() << endl;
	cout << curden << endl;
#endif

	// Read matrix B
	triplet_mat_file = input_location + "B.csv";

#if DEBUG_ANALYTICAL
	cout << "\nParsing the matrix B file..." << endl;
	cout << triplet_mat_file << endl;
#endif

	tripletParser(&triplet_mat_B);
	
	SpMat_l b_matrix(nodes_number, ports);

	// Initialize matrix B
	b_matrix.setFromTriplets(triplet_mat_B.begin(), triplet_mat_B.end());
	b_matrix.makeCompressed();


	// Read initial stress
	string init_stress_file_location = input_location + "initial_stress.csv";
	ifstream init_stress_file(init_stress_file_location);

	my_VectorXd initial_stress = my_VectorXd::Zero(b_matrix.rows());
	if (!init_stress_file) {  // Check if file exists
		// std::cerr << "No initial stress found. Set to zero." << std::endl;
	} else { // File found
		// std::cerr << "Found initial stress file." << std::endl;
		// count the number of lines in the input file
		num_lines = 0;
		while (std::getline(init_stress_file, line)) {
			num_lines++;
		}
		init_stress_file.close();

		// reopen the input file and read the values into my_vector
		init_stress_file.open(init_stress_file_location);
		i = 0;
		while (getline(init_stress_file, line)) {
			initial_stress(i) = stod(line); // double precision. Maybe going to change this
			i++;
		}
		init_stress_file.close();
	}
	
    // if (!initial_stress.isZero()) {
	//     cout << "Initial stress:\n";
	//     cout << initial_stress << endl;
    // }

	// Call analytical
	analytical(b_matrix, curden, initial_stress, output_location);

	// Beginning of writing the resulting stress
	string output_file_location = output_location + "stress_" + to_string(simulation_time) + ".txt";
	// Create the directory if it doesn't exist
	boost::filesystem::create_directories(output_file_location.substr(0, output_file_location.find_last_of("/\\")));

	// Writing the stress
#if DEBUG_ANALYTICAL
	cout << "\nWriting the stress...\n" << output_file_location << endl;
#endif
	ofstream output_file;
	output_file.open(output_file_location);
	output_file.precision(18);
	my_VectorXd stress = resulting_stress;

	for (int i = 0; i < stress.size(); i++) {
		output_file << stress(i) << std::endl;
	}

	output_file.close();
	// End of writing the resulting stress


	timings[1] = high_resolution_clock::now();

	/* Set the reduction time */
	exec_time = duration_cast<duration<PRECISION_TYPE>>(timings[1] - timings[0]).count();
}

void simulation_engine::dct1d(const my_VectorXd& in, my_VectorXd& out) {
	int size = in.size();
	out.resize(size);
	PRECISION_TYPE* in_ptr = const_cast<PRECISION_TYPE*>(in.data());
	PRECISION_TYPE* out_ptr = out.data();

	/* * * DCT-II * */
#if ENABLE_DOUBLES
	fftw_plan plan = fftw_plan_r2r_1d(size, in_ptr, out_ptr, FFTW_REDFT10, FFTW_ESTIMATE);
	fftw_execute(plan);
	fftw_destroy_plan(plan);
#else
	fftwf_plan plan = fftwf_plan_r2r_1d(size, in_ptr, out_ptr, FFTW_REDFT10, FFTW_ESTIMATE);
	fftwf_execute(plan);
	fftwf_destroy_plan(plan);
#endif

	fftw_cleanup();

	// Make the output orthogonal
	out(0) *= sqrt(1.0 / 4 / size);
	PRECISION_TYPE factor = sqrt(1.0 / 2 / size);
	for (int i = 1; i < size; i++)
		out(i) *= factor;
}

void simulation_engine::idct1d(const my_VectorXd& in, my_VectorXd& out) {
	const int size = in.rows();
	out.resize(size);

	// Unnormalize input
	out[0] = in[0] / sqrt(1.0 / 4.0 / size);
	double factor = sqrt(1.0 / 2.0 / size);
	for (int i = 1; i < size; i++)
		out[i] = in[i] / factor;

	fftw_plan plani = fftw_plan_r2r_1d(size, out.data(), out.data(), FFTW_REDFT01, FFTW_ESTIMATE);
	fftw_execute(plani);
	fftw_destroy_plan(plani);
	fftw_cleanup();

	// Scale the output to obtain the exact inverse
	for (int i = 0, f = size << 1; i < size; i++)
		out[i] /= f;
}

void simulation_engine::form_analytical_solution(my_VectorXd& lambdas, my_VectorXd& right_side_matrix, my_VectorXd& right_side_matrix2, const unsigned int nx_total, const SpMat_l& B, const my_VectorXd u, const my_VectorXd initial_stress) {
	
	my_VectorXd lambdas_temp(nx_total);
	my_VectorXd r, right_side_matrix_temp, right_side_matrix_temp2;

#if DEBUG_ANALYTICAL
	cout << "Inside form_analytical_solution " << std::endl;
#endif

	// Calculate lambdas 
	for (int i = 0; i < nx_total; i++) {
		lambdas_temp(i) = 2 * cos(i * M_PI / nx_total) - 2;
	}

	// Calculate vector B*u 
	r = B * u;

	// Perform DCT-II on vector B*u 
	dct1d(r, right_side_matrix_temp);

	// Perform DCT-II on vector initial stress 
	dct1d(initial_stress, right_side_matrix_temp2);


	lambdas = lambdas_temp;
	right_side_matrix = right_side_matrix_temp;
	right_side_matrix2 = right_side_matrix_temp2;

#if DEBUG_ANALYTICAL
	//cout << "RHS matrix: " << right_side_matrix << std::endl;
#endif
}

void simulation_engine::calc_analytical_solution(my_VectorXd& stress, const my_VectorXd& lambdas, const my_VectorXd& right_side_matrix, const my_VectorXd& right_side_matrix2, const unsigned int nx_total, const PRECISION_TYPE t) {
	// Calculate sigmas at specific time
	my_MatrixXd L = my_MatrixXd::Zero(nx_total, nx_total);
	my_MatrixXd L2 = my_MatrixXd::Zero(nx_total, nx_total);
	my_VectorXd q = my_VectorXd::Zero(nx_total);
	my_VectorXd q2 = my_VectorXd::Zero(nx_total);
	my_VectorXd stress_temp = my_VectorXd::Zero(nx_total);
	my_VectorXd stress_temp2 = my_VectorXd::Zero(nx_total);

	PRECISION_TYPE A_coeff = this->coeff;
	for (int i = 0; i < nx_total; i++) {
		if (lambdas(i) == 0) {
			L(i, i) = t;
		}
		else {
			L(i, i) = (exp(A_coeff * t * lambdas(i)) - 1) / (A_coeff * lambdas(i));
		}
	}

	for (int i = 0; i < nx_total; i++) {
		L2(i, i) = exp(A_coeff * t * lambdas(i));
	}

#if DEBUG_ANALYTICAL
	cout << "L matrix: " << L(0) << endl;
#endif

	// IDCT-II
	q = L * right_side_matrix;
	q2 = L2 * right_side_matrix2;

#if DEBUG_ANALYTICAL
	cout << "q(100): " << q(100) << endl;
	cout << "q2(100): " << q2(100) << endl;
#endif

	idct1d(q, stress_temp);
	idct1d(q2, stress_temp2);

#if DEBUG_ANALYTICAL
	cout << "stress_temp[100]: " << stress_temp(100) << endl;
	cout << "stress_temp2[100]: " << stress_temp2(100) << endl;
#endif

	stress = stress_temp + stress_temp2;
}

void simulation_engine::analytical(const SpMat_l& B, const my_VectorXd& curden, my_VectorXd& initial_stress, const string& output_location) {
	unsigned int n_size = B.rows();

#if DEBUG_ANALYTICAL
	cout << "\n\n\n-------- Analytical --------\n";
	cout << "B rows: " << B.rows() << " and B cols: " << B.cols() << std::endl;
#endif

	my_VectorXd lambdas;
	my_VectorXd right_side_matrix, right_side_matrix2;

	form_analytical_solution(lambdas, right_side_matrix, right_side_matrix2, B.rows(), B, curden, initial_stress);

#if DEBUG_ANALYTICAL
	cout << "form_analytical_solution done\n";
#endif

	// Calculate the stress at specific time
	PRECISION_TYPE t = simulation_time; //6.38e8;
	my_VectorXd stress;
	calc_analytical_solution(stress, lambdas, right_side_matrix, right_side_matrix2, B.rows(), t);
	this->resulting_stress = stress;

#if DEBUG_ANALYTICAL
	std::cout << "\n\n\n----- End of Analytical ----\n\n";
#endif
}