import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d

fig = plt.figure(figsize=(10,10)) #Define figure size
ax = fig.add_subplot(111, projection='3d')
plt.rcParams['legend.fontsize'] = 20

np.random.seed(4294967294) #Used the random seed for consistency

mu_vec_1 = np.array([0,0,0])
cov_mat_1 = np.array([[1,0,0],[0,1,0],[0,0,1]])
class_1_sample = np.random.multivariate_normal(mu_vec_1, cov_mat_1, 30).T
assert class_1_sample.shape == (3,30), "The matrix dimensions is not 3x30"

mu_vec_2 = np.array([1,1,1])
cov_mat_2 = np.array([[1,0,0],[0,1,0],[0,0,1]])
class_2_sample = np.random.multivariate_normal(mu_vec_2, cov_mat_2, 30).T
assert class_2_sample.shape == (3,30), "The matrix dimensions is not 3x30"

ax.plot(class_1_sample[0,:], class_1_sample[1,:], class_1_sample[2,:], 'o', markersize=10, color='green', alpha=1.0, label='Class 1')
ax.plot(class_2_sample[0,:], class_2_sample[1,:], class_2_sample[2,:], 'o', markersize=10, alpha=1.0, color='red', label='Class 2')

plt.title('Data Samples for Classes 1 & 2', y=1.04)
ax.legend(loc='upper right')
plt.savefig('Multivariate_distr.png', bbox_inches='tight')
plt.show()
