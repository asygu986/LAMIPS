import scipy.io as sio  # 读取.mat文件
import numpy as np
x_mat = sio.loadmat("opt_path\\x_traj.mat")
y_mat = sio.loadmat("opt_path\\y_traj.mat")
x_cycle = np.asarray(x_mat['vector1']).flatten().astype(float)
y_cycle = np.asarray(y_mat['vector2']).flatten().astype(float)

# print(x_mat)
print(y_cycle*1000)