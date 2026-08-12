
# # # # FFTW3 # # # #

## Not correct: sudo apt-get install -y fftw3

## Correct:
# download the tar.gz FFTW3: https://fftw.org/download.html & extract
# sugkekrimena: https://fftw.org/fftw-3.3.10.tar.gz
tar zxvf fftw-VERSION.tar.gz # extract
cd fftw-VERSION/ # go inside the folder
# inside the extracted folder, do:
./configure --enable-threads --enable-omp --enable-avx
sudo make
sudo make install


# # # # EIGEN # # # # 

# Download from http://eigen.tuxfamily.org/index.php?title=Main_Page#Download
# sugkekrimena: https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz

# # # # BOOST # # # #
sudo apt-get install libboost-all-dev

https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl-download.html?operatingsystem=linux&distributions=online
