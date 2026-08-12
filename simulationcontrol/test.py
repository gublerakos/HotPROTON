import math

def compute_previous_ttf(r_value):
    return math.sqrt(-math.log(r_value))

# Example usage
previous_r_values = [0.99997506278, 0.999999592934, 0.954187739638, 0.999965845169]

previous_ttf_values = [compute_previous_ttf(r) for r in previous_r_values]

print("Computed previous TTF values:", previous_ttf_values)