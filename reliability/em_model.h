#include <cmath>

class EM_model : public Rmodel {
    using Rmodel::Rmodel;

   public:
    void update_timestamp(long double new_time_stamp, long double temperature) {
        long double delta_t = new_time_stamp - current_time_stamp;
        current_time_stamp = new_time_stamp;
        update(delta_t, temperature);
    }


    void update(long double delta_t, long double temperature) {
        if (delta_t < 0) {
            throw std::runtime_error("Negative delta_t is not allowed");
        }

    /* Calculate the new R value.
     * temp in celsius
     * new_time_stamp in ms

       We use equation (5) from the paper [1] (equation (11) in [2]):
       R(t) = exp(-pow((sum(T_j / alpha(T_j))), beta))

       [1] : "Lightweight and Open-source Framework for the Lifetime Estimation
       of Multicore Systems" 2014 by Cristiana Bolchini et al.
       [2] : "System-level reliability modeling for MPSoCs" by Yan Xiang.
       */

        // Add measurement to the stored 'current_state': sum(T_j / alpha(T_j))
        current_state += delta_t / alpha(temperature);

        long double new_R = expl(-1 * powl(current_state, BETA));
        if (new_R > current_R) {
            throw std::runtime_error("Reliability cannot increase over time");
        }
        area_under_curve += new_R * delta_t;
        current_R = new_R;
    }

   private:

    /* Wearout scale function for the EM fault model.
     *  temp in celsius. */
    long double alpha(long double temp) {
        long double temp_kelvin = celsius_to_kelvin(temp);
        return (CONST_A0 * pow(CONST_JMJCRIT, -CONST_N) *
                exp(ACTIVATIONENERGY / (BOLTZMANCONSTANT * temp_kelvin))) /
               CONST_ERRF;
    }

    long double celsius_to_kelvin(long double temp) { return temp + ZERO_CEL_IN_KELVIN; }

    // Electro-Migration related parameters

    const long double BETA = 2; // weibull scaling parameter (for CONST_ERRF)
    const long double ACTIVATIONENERGY = 0.48;
    // const long double ACTIVATIONENERGY = 0.8;  // From JEDEC page 5.
    const long double BOLTZMANCONSTANT = 8.6173324 * 0.00001;
    const long double CONST_JMJCRIT = 1500000;
    const long double CONST_N = 1.1;
    // const long double CONST_N = 2.0;  // From JEDEC page 5.
    const long double CONST_ERRF = 0.88623;  // math.gamma(1 + 1/BETA)
    const long double CONST_A0 = 30000;  // cross section = 1um^2  material constant = 3*10^13
    // Thermal model parameters
    const long double ZERO_CEL_IN_KELVIN = 273.15;
};
