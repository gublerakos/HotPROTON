import numpy as np
import pandas as pd
from pandas import DataFrame

import seaborn as sns
import matplotlib.pyplot as plt

# Read data from file.
data = pd.read_csv("time-R.csv")

print(data)

# Plot R over time.
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots()
ax.set_title('R over time')
sns.scatterplot(data=data, x="time", y="R")
plt.show()

