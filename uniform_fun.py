import numpy as np
import tensorflow as tf


def traj_centered(x_trajectory, y_trajectory, Lx, Ly):
    ## 居中操作
    # 计算轨迹的最小值、最大值和中心点
    x_min, x_max = np.min(x_trajectory), np.max(x_trajectory)
    y_min, y_max = np.min(y_trajectory), np.max(y_trajectory)

    x_center_traj = (x_max + x_min) / 2
    y_center_traj = (y_max + y_min) / 2

    # 计算图像的中心点
    x_center_fig = Lx / 2
    y_center_fig = Ly / 2

    # 将轨迹中心移动到图像中心
    x_trajectory_centered = x_trajectory - x_center_traj + x_center_fig
    y_trajectory_centered = y_trajectory - y_center_traj + y_center_fig
    return x_trajectory_centered, y_trajectory_centered


def traj_centered_tensor(x_trajectory, y_trajectory, Lx, Ly):
    # 使用 TensorFlow 操作计算轨迹的最小值、最大值和中心点
    x_min = tf.reduce_min(x_trajectory)
    x_max = tf.reduce_max(x_trajectory)
    y_min = tf.reduce_min(y_trajectory)
    y_max = tf.reduce_max(y_trajectory)

    x_center_traj = (x_max + x_min) / 2
    y_center_traj = (y_max + y_min) / 2

    # 计算图像的中心点
    x_center_fig = Lx / 2
    y_center_fig = Ly / 2

    # 将轨迹中心移动到图像中心
    x_trajectory_centered = x_trajectory - x_center_traj + x_center_fig
    y_trajectory_centered = y_trajectory - y_center_traj + y_center_fig

    return x_trajectory_centered, y_trajectory_centered


# 激光上各店轨迹参数
def laser_trajectory(t, x_trajectory, y_trajectory,nz):
    """根据自定义轨迹计算激光中心的位置"""
    x_center = x_trajectory[t]
    y_center = y_trajectory[t]
    z_center = nz // 2  # 固定 z 方向
    return x_center, y_center, z_center


