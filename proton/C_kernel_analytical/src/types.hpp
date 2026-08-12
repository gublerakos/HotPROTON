#ifndef TYPES_HPP_
#define TYPES_HPP_

#include <string>
#include <vector>
#include <Eigen/Sparse>

using namespace std;

#define ENABLE_DOUBLES 1

#if ENABLE_DOUBLES
	#define PRECISION_TYPE double
#else
	#define PRECISION_TYPE float
#endif

#define _USE_MATH_DEFINES

/* Debug Flags */
#define DEBUG_ANALYTICAL 0

/* matrix/vector types */
typedef Eigen::Triplet<PRECISION_TYPE> eigen_triplet_T;								// A data structure for the TRIPLET format
typedef std::vector<eigen_triplet_T> eigen_triplet_vector_T;						// A vector of eigen_triplet_T
typedef Eigen::Matrix<PRECISION_TYPE, Eigen::Dynamic, Eigen::Dynamic> my_MatrixXd;	// A data structure for dense matrices
typedef Eigen::Matrix<PRECISION_TYPE, Eigen::Dynamic, 1> my_VectorXd;				// A data structure for dense vectors
typedef Eigen::SparseMatrix<PRECISION_TYPE> SpMat;									// A data structure for sparse matrices

#if CHOLMOD_SOLVER && ENABLE_DOUBLES
	typedef SuiteSparse_long storage_index_T;
#else
	typedef int storage_index_T;
#endif

typedef Eigen::SparseMatrix<PRECISION_TYPE,0, storage_index_T> SpMat_l;

#if ENABLE_DOUBLES
	typedef Eigen::VectorXcd my_VectorXcd;
	typedef Eigen::VectorXd eigen_vector_T;
#else
	typedef Eigen::VectorXcf my_VectorXcd;
	typedef Eigen::VectorXf eigen_vector_T;
#endif

#endif /* TYPES_HPP_ */
