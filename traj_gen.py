import numpy as np
import math
import scipy.io as sio  # 读取.mat文件

# 刀具轨迹生成函数
def cutter_trajectory(con, coordinates):
    """
    计算多段直线连接的刀具轨迹

    输入参数：
        tbs: 时间数组，单位：秒 (s)
        con: 全局参数集合
        cutter_traj_type: 刀具轨迹类型，"line" - 直线，"sin" - 正弦波
        params: 轨迹参数
        coordinates: 坐标列表，包含多个点

    输出参数：
        x_cutter: 刀具X坐标数组，单位：米 (m)
        y_cutter: 刀具Y坐标数组，单位：米 (m)
        segment_info: 分段信息
    """
    # 检查坐标数量
    if len(coordinates) < 2:
        print("警告：坐标数量不足，需要至少两个点")
        # 使用默认起点 (0,0) 和 (0.01, 0) 作为终点
        coordinates = [(0.0, 0.0), (0.01, 0.0)]

    # 获取进给速度
    X0Cutter = con['X0Cutter']  # 刀具初始X位置
    Y0Cutter = con['Y0Cutter']  # 刀具初始Y位置

    # fx = con['fx']  # X轴进给速度
    # fy = con['fy']  # 假设fy=0
    # fv = math.sqrt(fx ** 2) # 不考虑y轴进给速度
    fv = con["fv"]

    if fv == 0:
        print("警告：进给速度为0，无法生成轨迹")
        return {}

    # 计算总路径长度和每段信息
    total_length = 0
    segments = []


    for i in range(len(coordinates) - 1):
        start_point = coordinates[i]
        end_point = coordinates[i + 1]

        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        segment_length = math.sqrt(dx ** 2 + dy ** 2) # 每段长度

        if segment_length == 0:
            print(f"警告：第{i + 1}段长度为0，跳过")
            continue

        # 计算方向余弦
        cos_theta = dx / segment_length
        sin_theta = dy / segment_length

        # 计算该段运动所需时间
        segment_time = segment_length / fv  # 原本为fv

        segment_info = {
            'index': i,
            'start_point': start_point,
            'end_point': end_point,
            'length': segment_length,
            'dx': dx,
            'dy': dy,
            'cos_theta': cos_theta,
            'sin_theta': sin_theta,
            'time': segment_time,
            'start_time': total_length / fv,  # 每一段刀具轨迹的开始时间
            'end_time': (total_length + segment_length) / fv # 每一段刀具轨迹的结束时间
        }

        segments.append(segment_info)
        total_length += segment_length

    # 获取刀具轨迹点
    x_cutter=np.zeros(len(coordinates))
    y_cutter=np.zeros(len(coordinates))
    for j in range(len(coordinates)):
        x_cutter[j]=coordinates[j][0]
        y_cutter[j]=coordinates[j][1]


    if total_length == 0:
        print("警告：总路径长度为0，无法生成轨迹")
        return {}

    # 计算总时间
    total_time = total_length / fv
    return x_cutter, y_cutter, {'segments': segments, 'total_length': total_length, 'total_time': total_time}


# ===================== 你提供的三个核心函数（仅修复rotate_coordinates，其他完全不变） =====================
def calculate_theta(x_cutter_v, y_cutter_v, t):
    """
    计算瞬时运动方向角 (theta)，基于刀具的速度梯度
    """
    v_x = np.gradient(x_cutter_v, t)
    v_y = np.gradient(y_cutter_v, t)
    theta = np.arctan2(v_y, v_x)
    return theta


def dynamic_angle_factor(theta, t, base_factor=1, sharpness_factor=0.5):
    """
    基于theta变化率动态调整角度因子
    """
    theta_rate = np.gradient(theta, t)
    angle_factor = base_factor / (1 + sharpness_factor * np.abs(theta_rate))
    return angle_factor


def rotate_coordinates(x_laser, y_laser, x_cutter, y_cutter, theta):
    """
    坐标系变换函数（带距离保持）→ 修复维度报错，完全兼容数组输入
    """
    # 将激光坐标平移到以刀具位置为原点
    x_laser_translated = x_laser - x_cutter
    y_laser_translated = y_laser - y_cutter

    # 向量化旋转计算，适配任意长度的数组
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    x_rotated = x_laser_translated * cos_t - y_laser_translated * sin_t + x_cutter
    y_rotated = x_laser_translated * sin_t + y_laser_translated * cos_t + y_cutter

    return x_rotated, y_rotated


# 注意，这里的x坐标一定不能为负值
def sweeping_laser_trajectory_with_distance_preservation(con, traj_params, x_cutter, y_cutter, cutter_info):
    """
    生成带动态旋转与按段去重/延申的激光扫描轨迹：
    scWidth: 激光宽度；N：控制激光点密集程度
    - 对每段，在段末沿刀具轨迹方向"向后"延申Ret长度；
    - 从第二段起，去掉该段起点沿刀具轨迹Ret长度内的激光轨迹，避免与上一段重叠。
    """
    # 计算轨迹用参数
    traj_type = traj_params['trajectory_type'].lower()
    params = traj_params['params']
    ae = con["ae"]
    ret_real = con['ret']  # 有效铣刀半径

    ret_v = 26e-3     # 用于改变激光轨迹曲率的铣刀半径
    laser_r = con['laser_r']  # 激光束半径
    # fz = con["fz"]  # 每齿进给量
    tooth_number = con["tooth_number"]
    fv = con["fv"]*1.185

    dt = con["dt"]  # 时间步长，即激光两点之间间隔时间
    base_factor = con["base_factor"]
    sharpness_factor = con["sharpness_factor"]

    # 计算各段路径长度和方向向量即坐标
    seg_lengths=[]
    cos_theta=[]
    sin_theta=[]
    for i in range(len(cutter_info['segments'])):
        seg_lengths.append(cutter_info['segments'][i]["length"])
        cos_theta.append(cutter_info['segments'][i]["cos_theta"])
        sin_theta.append(cutter_info['segments'][i]["sin_theta"])
    total_length = cutter_info["total_length"]

    # 获得激光轨迹
    Lw = ae + 2 * laser_r  # 考虑到激光源半径后的扫描半径
    gm = 2 * np.arcsin(Lw / 2 / ret_v)  # 激光扫描角度范围
    L1 = 2 * ret_v * gm
    # fr = fz * tooth_number  # 每转进给距离 (m/r)
    fv = fv / 60   # 进给速率 (m/s)
    vLaser1 = tooth_number * L1 * fv / laser_r / 2
    T1 = L1 / vLaser1  # 激光扫描过一个周期的时间

    point_of_one_pass = round(T1 / dt)  # 一个周期内扫描点数，是根据一个周期总长除以激光时间步长而
    # print(point_of_one_pass)

    if total_length == 0:
        total_length = 0.01

    # ===================== 轨迹生成（100%还原你的原始逻辑+时间延迟防重叠） =====================
    laser_length = np.zeros(len(seg_lengths))

    period_num = []
    tbs = []
    x_cutter_v = []
    y_cutter_v = []
    xbs = []
    ybs = []

    for i in range(len(seg_lengths)):
        laser_length[i] = seg_lengths[i] + ret_real
        Tc = laser_length[i] / fv # 刀具移动时间
        period_num.append(Tc / T1)


        # ✅【完全还原你的时间延迟代码】防止轨迹重叠！！！
        if i == 0:
            tbs.append(np.linspace(0, round(period_num[i]) * T1, round(period_num[i]) * (point_of_one_pass + 1)))
            # print("优化前各段周期数", round(period_num[i]))
        elif (x_cutter[i+1],y_cutter[i+1]) == (x_cutter[0], y_cutter[0]):  # 用于当加工一个闭合面时激光免于重合
            tbs.append(np.linspace(11 * T1, (round(period_num[i]) -20)* T1, round(period_num[i]) * (point_of_one_pass + 1)))
        else:
            tbs.append(np.linspace(11 * T1, round(period_num[i]) * T1, round(period_num[i]) * (point_of_one_pass + 1)))
            # print("优化前各段周期数", round(period_num[i])-8)



        # 你的原始刀具虚拟轨迹逻辑（完全不变）
        x_cutter_v.append(x_cutter[i] + fv * cos_theta[i] * tbs[i])
        y_cutter_v.append(y_cutter[i] + fv * sin_theta[i] * tbs[i])

        # 调用函数计算瞬时方向角
        theta = calculate_theta(x_cutter_v[i], y_cutter_v[i], tbs[i])
        # 动态角度因子
        angle_factor = dynamic_angle_factor(theta, tbs[i], base_factor=base_factor, sharpness_factor=sharpness_factor)
        theta_adjusted = theta * angle_factor

        # 你的原始激光局部轨迹（完全不变）
        phi_b = -gm * np.cos(2 * np.pi / T1 * tbs[i]) / 2
        x_laser_local = x_cutter_v[i] + ret_v * np.cos(phi_b)-ret_v
        y_laser_local = y_cutter_v[i] + ret_v * np.sin(phi_b)
        # 动态旋转激光轨迹
        x_rot, y_rot = rotate_coordinates(
            x_laser_local, y_laser_local,
            x_cutter_v[i], y_cutter_v[i],
            theta_adjusted
        )

        xbs.append(x_rot)
        ybs.append(y_rot)

    # 展平轨迹点（原始逻辑不变）
    # xbs = np.concatenate(xbs)
    # ybs = np.concatenate(ybs)
    #
    # x_rotated = xbs
    # y_rotated = ybs
    return xbs, ybs, vLaser1


# 这是获取优化后的激光轨迹
def sweeping_laser_trajectory_optimized(con, traj_params, x_cutter, y_cutter, cutter_info):
    """
    优化激光轨迹代码
    """
    # ===================== 1. 参数初始化（统一优质代码变量名） =====================
    traj_type = traj_params['trajectory_type'].lower()
    params = traj_params['params']

    # 核心物理参数（与优质代码完全对齐）
    ae = con["ae"]
    ret = con['ret']  # 有效铣刀半径
    laser_r = con['laser_r']  # 激光束半径
    # fz = con["fz"]  # 每齿进给量
    tooth_number = con["tooth_number"]
    # nr = con["nr"]
    fv = con["fv"]  # 进给速率（mm/min)
    # dt = con["dt"]  # 时间步长，即激光两点之间间隔时间
    base_factor = con["base_factor"]
    sharpness_factor = con["sharpness_factor"]

    # 刀具分段信息（从坐标提取，替代原复杂cutter_trajectory）
    seg_lengths = []
    cos_theta = []
    sin_theta = []
    for i in range(len(cutter_info['segments'])):
        seg_lengths.append(cutter_info['segments'][i]["length"])
        cos_theta.append(cutter_info['segments'][i]["cos_theta"])
        sin_theta.append(cutter_info['segments'][i]["sin_theta"])
    total_length = cutter_info["total_length"]

    # ===================== 2. 激光基础参数（与优质代码完全一致） =====================
    Lw = ae + 2 * laser_r  # 考虑到激光源半径后的扫描半径
    gm = 2 * np.arcsin(Lw / 2 / ret)
    L1 = 2 * ret * gm
    # fr = fz * tooth_number
    fv = fv / 60
    vLaser1 = tooth_number * L1 * fv / laser_r / 2
    # T1 = L1 / vLaser1  # 激光单周期时间

    # ===================== 3. 加载【.mat优化轨迹】（核心功能保留） =====================
    x_mat = sio.loadmat("opt_path\\x_traj.mat")
    y_mat = sio.loadmat("opt_path\\y_traj.mat")
    x_cycle = np.asarray(x_mat['vector1']).flatten().astype(float)
    y_cycle = np.asarray(y_mat['vector2']).flatten().astype(float)

    # ===================== 新增核心：缩放 + 平移（精准满足要求） =====================
    y_min = np.min(y_cycle)
    y_max = np.max(y_cycle)
    original_height = y_max - y_min
    target_height = 2 * ret
    scale_factor = target_height / original_height
    y_scaled = y_cycle * scale_factor
    x_final = []
    y_final = []

    for h in range(len(seg_lengths)):
        target_start_x = x_cutter[h] + sin_theta[h] * ret*0.9
        target_start_y = y_cutter[h] - cos_theta[h] * ret*0.9
        if h>0:
            target_start_x=target_start_x+cos_theta[h] * ret
            target_start_y=target_start_y+sin_theta[h] * ret
        x_final.append(x_cycle + (target_start_x - x_cycle[0]))
        y_final.append(y_scaled + (target_start_y - y_scaled[0]))

    step = (x_cycle.max() - x_cycle.min()) * 0.65

    # ===================== 4. 分段生成轨迹（🔥 已修改：增加方向旋转） =====================
    laser_length = np.zeros(len(seg_lengths))

    # ===================== 3. 分段生成轨迹（每段内所有周期拼接为一个数组） =====================
    xbs = []  # 每个元素是一段刀具轨迹对应的激光轨迹x坐标数组
    ybs = []  # 每个元素是一段刀具轨迹对应的激光轨迹y坐标数组

    for i in range(len(seg_lengths)):
        laser_length[i] = seg_lengths[i] + ret
        # print(round(laser_length[i] / step))
        assert isinstance(laser_length[i], (float, int, np.number)), "laser_length[i] is not a number"
        assert isinstance(step, (float, int, np.number)), "step is not a number"
        if i == 0:
            period_num = round(laser_length[i] / step+1e-9)-1
        elif (x_cutter[i+1],y_cutter[i+1]) == (x_cutter[0], y_cutter[0]):  # 用于当加工一个闭合面时激光免于重合
            period_num = round((seg_lengths[i]-2*ret) / step+ 1e-9)-1
        else:
            period_num = round(seg_lengths[i] / step+ 1e-9)-1
        # print("优化后各段周期数", period_num)

        # 获取当前段未旋转的轨迹（已平移至起点）
        x_local = x_final[i]   # 数组
        y_local = y_final[i]   # 数组
        start_x = x_local[0]
        start_y = y_local[0]
        cos = cos_theta[i]
        sin = sin_theta[i]

        # 绕起点旋转到刀具方向
        dx = x_local - start_x
        dy = y_local - start_y
        x_rot = start_x + dx * cos - dy * sin
        y_rot = start_y + dx * sin + dy * cos
        # 收集当前段所有周期的轨迹点（拼接）
        seg_x_list = []
        seg_y_list = []
        # 收集当前段所有周期的轨迹点（拼接）
        for j in range(period_num):
            # 每个周期的轨迹（数组）
            x_period = x_rot + j * step * cos
            y_period = y_rot + j * step * sin
            seg_x_list.append(x_period)
            seg_y_list.append(y_period)
        # 将当前段的所有周期拼接成一个完整的一维数组
        xbs.append(np.concatenate(seg_x_list))
        ybs.append(np.concatenate(seg_y_list))

    # ===================== 5. 轨迹后处理（优质代码逻辑） =====================

    return xbs, ybs, vLaser1