import numpy as np
import math


# 刀具轨迹生成函数
def cutter_trajectory(t, con, cutter_traj_type, params, coordinates):
    """
    计算多段直线连接的刀具轨迹

    输入参数：
        t: 时间数组，单位：秒 (s)
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
    X0Cutter = con[10]  # 刀具初始X位置
    Y0Cutter = con[11]  # 刀具初始Y位置

    fx = con[15]  # X轴进给速度
    fy = con[16]  # 假设fy=0
    fv = math.sqrt(fx ** 2 + fy ** 2)

    if fv == 0:
        print("警告：进给速度为0，无法生成轨迹")
        return np.zeros(len(t)), np.zeros(len(t)), {}

    # 计算总路径长度和每段信息
    total_length = 0
    segments = []

    for i in range(len(coordinates) - 1):
        start_point = coordinates[i]
        end_point = coordinates[i + 1]

        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        segment_length = math.sqrt(dx ** 2 + dy ** 2)

        if segment_length == 0:
            print(f"警告：第{i + 1}段长度为0，跳过")
            continue

        # 计算方向余弦
        cos_theta = dx / segment_length
        sin_theta = dy / segment_length

        # 计算该段所需时间
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
            'start_time': total_length / fv,  # 累积时间
            'end_time': (total_length + segment_length) / fv
        }

        segments.append(segment_info)
        total_length += segment_length

    if total_length == 0:
        print("警告：总路径长度为0，无法生成轨迹")
        return np.zeros(len(t)), np.zeros(len(t)), {}

    # 计算总时间
    total_time = total_length / fv

    # 初始化输出数组
    x_cutter = np.zeros(len(t))
    y_cutter = np.zeros(len(t))

    # 计算每个时间点对应的位置
    for idx, time_val in enumerate(t):
        # 归一化时间到[0, total_time]
        if time_val < 0:
            time_val = 0
        elif time_val > total_time:
            time_val = total_time

        # 查找当前时间属于哪一段
        current_segment = None
        local_time = 0

        for seg in segments:
            if time_val >= seg['start_time'] and time_val <= seg['end_time']:
                current_segment = seg
                local_time = time_val - seg['start_time']
                break

        # 如果时间超出所有段，使用最后一段的终点
        if current_segment is None:
            last_seg = segments[-1]
            x_cutter[idx] = last_seg['end_point'][0]
            y_cutter[idx] = last_seg['end_point'][1]
            continue

        # 计算在当前段中的归一化时间
        if current_segment['time'] > 0:
            normalized_t = local_time / current_segment['time']
        else:
            normalized_t = 0

        # 限制在0到1之间
        normalized_t = max(0, min(1, normalized_t))

        # 计算沿当前段的位移
        s = normalized_t * current_segment['length']

        # 根据轨迹类型计算坐标
        if cutter_traj_type == "line":
            # 直线轨迹
            x_cutter[idx] = current_segment['start_point'][0] + s * current_segment['cos_theta']
            y_cutter[idx] = current_segment['start_point'][1] + s * current_segment['sin_theta']

        elif cutter_traj_type == "sin":
            # X方向：匀速直线运动
            x_cutter = X0Cutter + fx * t
            amplitude = params.get("amplitude")  # 注意使用小括号
            frequency = params.get("frequency")
            y_cutter = Y0Cutter + amplitude * np.sin(frequency * t)

        elif cutter_traj_type == "zigzag":
            # 锯齿波轨迹
            num_zigzags = params.get("num_zigzags", 3)
            amplitude_zigzag = params.get("amplitude_zigzag", 0.009)
            period = params.get("period", 6.28)

            # 计算相位
            phase = 2 * np.pi * num_zigzags * normalized_t

            # 垂直方向单位向量
            perp_cos = -current_segment['sin_theta']
            perp_sin = current_segment['cos_theta']

            # 创建锯齿波
            zigzag = amplitude_zigzag * (
                        2 * np.abs(2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))) - 1)

            # 生成轨迹
            x_cutter[idx] = current_segment['start_point'][0] + s * current_segment['cos_theta'] + zigzag * perp_cos
            y_cutter[idx] = current_segment['start_point'][1] + s * current_segment['sin_theta'] + zigzag * perp_sin

        else:
            # 默认直线轨迹
            x_cutter[idx] = current_segment['start_point'][0] + s * current_segment['cos_theta']
            y_cutter[idx] = current_segment['start_point'][1] + s * current_segment['sin_theta']

    return x_cutter, y_cutter, {'segments': segments, 'total_length': total_length, 'total_time': total_time}


def calculate_theta(x_cutter, y_cutter, t):
    """
    计算瞬时运动方向角 (theta)，基于速度梯度

    输入参数：
        x_cutter: 刀具X坐标数组，单位：米 (m)
        y_cutter: 刀具Y坐标数组，单位：米 (m)
        t: 时间数组，单位：秒 (s)

    输出参数：
        theta: 瞬时运动方向角数组，单位：弧度 (rad)
    """
    # 计算速度分量（数值微分）
    v_x = np.gradient(x_cutter, t)  # dx/dt
    v_y = np.gradient(y_cutter, t)  # dy/dt

    # 计算每个时间点的角度
    theta = np.arctan2(v_y, v_x)  # 使用arctan2获得正确的象限

    return theta


def dynamic_angle_factor(theta, t, base_factor=1, sharpness_factor=0.5):
    """
    基于theta变化率动态调整角度因子

    输入参数：
        theta: 角度数组，单位：弧度 (rad)
        t: 时间数组，单位：秒 (s)
        base_factor: 基础角度因子，默认值 1
        sharpness_factor: 尖锐度因子，默认值 0.5

    输出参数：
        angle_factor: 动态调整后的角度因子数组
    """
    # 计算theta的变化率（dtheta/dt）
    theta_rate = np.gradient(theta, t)
    # 基于theta变化率计算角度因子
    angle_factor = base_factor / (1 + sharpness_factor * np.abs(theta_rate))

    return angle_factor


def rotate_coordinates(x_laser, y_laser, x_cutter, y_cutter, theta):
    """
    坐标系变换函数（带距离保持）

    输入参数：
        x_laser: 激光原始X坐标，单位：米 (m)
        y_laser: 激光原始Y坐标，单位：米 (m)
        x_cutter: 刀具当前位置X坐标，单位：米 (m)
        y_cutter: 刀具当前位置Y坐标，单位：米 (m)
        theta: 旋转角度，单位：弧度 (rad)

    输出参数：
        x_rotated: 旋转后的X坐标，单位：米 (m)
        y_rotated: 旋转后的Y坐标，单位：米 (m)
    """
    # 将激光坐标平移到以刀具位置为原点
    x_laser_translated = x_laser - x_cutter
    y_laser_translated = y_laser - y_cutter

    # 旋转矩阵
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])

    # 应用旋转
    xy_rotated = np.dot(R, np.array([x_laser_translated, y_laser_translated]))

    # 平移回原始坐标系
    x_rotated = xy_rotated[0] + x_cutter
    y_rotated = xy_rotated[1] + y_cutter

    return x_rotated, y_rotated

# 注意，这里的x坐标一定不能为负值
def sweeping_laser_trajectory_with_distance_preservation(scWidth, con, N, traj_params, coordinates):
    """
    生成带动态旋转与按段去重/延申的激光扫描轨迹：
    scWidth: 激光宽度；N：控制激光点密集程度
    - 对每段，在段末沿刀具轨迹方向"向后"延申Ret长度；
    - 从第二段起，去掉该段起点沿刀具轨迹Ret长度内的激光轨迹，避免与上一段重叠。
    """
    traj_type = traj_params['trajectory_type'].lower()
    params = traj_params['params']

    Ret = con[5]  # 有效铣刀半径
    rb0 = con[7]  # 激光束半径
    base_factor = con[26]
    sharpness_factor = con[27]

    point_of_one_pass = N * con[25]  # con[25]=100， 精确程度
    Rb = Ret # 这里直接认为刀具有效半径等于铣刀半径
    gm = 2 * np.arcsin(scWidth / 2 / Rb)  # 激光扫描角度范围

    # 计算总路径长度
    total_length = 0.0
    seg_lengths = []
    for i in range(len(coordinates) - 1):
        dx = coordinates[i + 1][0] - coordinates[i][0]
        dy = coordinates[i + 1][1] - coordinates[i][1]
        L = math.hypot(dx, dy)
        seg_lengths.append(L)
        total_length += L
    if total_length == 0:
        total_length = 0.01

    # 合速度与总时间
    fx = con[15]  # X轴进给速度
    fy = con[16]  # Y轴进给速度，假设为0
    fv = math.sqrt(fx ** 2 + fy ** 2)
    total_time = total_length / fv

    # 获取刀具轨迹段信息
    # 为了获取段信息，先生成一个基础时间序列
    tbs_temp = np.linspace(0.0, total_time, point_of_one_pass + 1)
    _, _, seg_info = cutter_trajectory(tbs_temp, con, traj_type, params, coordinates)
    segments = seg_info['segments'] if isinstance(seg_info, dict) and 'segments' in seg_info else []

    # 计算每段基础时间长度和延申时间
    seg_base_times = []
    for seg in segments:
        seg_base_times.append(seg['time'])

    ext_time = Ret / fv  # 延申Ret长度所需时间
    # 构建新的时间序列：每段基础时间 + 延申时间
    # 总时间 = 所有段基础时间 + 段数 × 延申时间
    new_total_time = total_time + len(segments) * ext_time

    # 计算每段在新时间序列中的起始和结束时间
    seg_new_start_times = []
    seg_new_end_times = []
    current_time = 0.0

    for i, seg_base_time in enumerate(seg_base_times):
        seg_new_start_times.append(current_time)
        # 段的基础部分
        current_time += seg_base_time
        # 段的延申部分
        current_time += ext_time
        seg_new_end_times.append(current_time)

    # 生成完整的时间序列（包含所有延申）
    # 重新分配点数：每段的基础点数 + 延申点数
    total_points = point_of_one_pass + len(segments) * int(ext_time / (total_time / point_of_one_pass))
    tbs_full = np.linspace(0.0, new_total_time, total_points + 1)

    # 计算刀具轨迹（包含延申）
    # 需要修改cutter_trajectory函数以支持带延申的时间序列
    # 这里我们手动计算
    x_cutter_full = np.zeros_like(tbs_full)
    y_cutter_full = np.zeros_like(tbs_full)

    # 为每段计算刀具位置
    for i, seg in enumerate(segments):
        seg_start = seg_new_start_times[i]
        seg_end_base = seg_start + seg['time']  # 基础部分结束
        seg_end_ext = seg_new_end_times[i]  # 延申部分结束

        # 找到属于当前段的时间点
        seg_mask = (tbs_full >= seg_start) & (tbs_full <= seg_end_ext)
        seg_times = tbs_full[seg_mask]

        # 归一化时间
        for j, t in enumerate(seg_times):
            idx = np.where(tbs_full == t)[0][0]

            if t <= seg_end_base:
                # 基础部分：沿线段运动
                local_time = t - seg_start
                normalized_t = local_time / seg['time'] if seg['time'] > 0 else 0
                normalized_t = max(0, min(1, normalized_t))
                s = normalized_t * seg['length']

                x_cutter_full[idx] = seg['start_point'][0] + s * seg['cos_theta']
                y_cutter_full[idx] = seg['start_point'][1] + s * seg['sin_theta']
            else:
                # 延申部分：继续沿原方向运动
                local_time = t - seg_end_base
                s_ext = local_time * fv  # 延申距离

                x_cutter_full[idx] = seg['end_point'][0] + seg['cos_theta'] * s_ext
                y_cutter_full[idx] = seg['end_point'][1] + seg['sin_theta'] * s_ext

    # 方向角与动态因子
    theta_dynamic = calculate_theta(x_cutter_full, y_cutter_full, tbs_full)
    angle_factors = dynamic_angle_factor(theta_dynamic, tbs_full, base_factor, sharpness_factor)

    # 激光扫描学参数
    L1 = 2 * Rb * gm
    insertNr = 4
    vLaser1 = insertNr * L1 / rb0 / 2 * fx
    T1 = L1 / vLaser1

    # 激光原始坐标（未旋转）
    phi_b = -gm * np.cos(2 * np.pi / T1 * tbs_full) / 2
    xbs = x_cutter_full + Rb * np.cos(phi_b)
    ybs = y_cutter_full + Rb * np.sin(phi_b)
    #(Ret/0.01)*2 *，实际上啊，这里并不需要乘上一个系数，因为铣削宽度就影响了激光扫描半径和切削区域对应的中心角
    # 平移，使初始点对齐
    xbs = xbs - xbs[0]

    # 应用动态旋转
    x_rotated_full = np.empty_like(xbs)
    y_rotated_full = np.empty_like(ybs)
    for i in range(len(tbs_full)):
        theta_adjusted = theta_dynamic[i] * angle_factors[i]
        xr, yr = rotate_coordinates(xbs[i], ybs[i], x_cutter_full[i], y_cutter_full[i], theta_adjusted)
        x_rotated_full[i] = xr
        y_rotated_full[i] = yr

    # 构建掩码：去掉每段起点处Ret长度内的激光点（从第二段开始）
    keep = np.ones(len(tbs_full), dtype=bool)

    for i in range(1, len(segments)):  # 从第二段开始
        seg_start_t = seg_new_start_times[i]
        start_idx = int(np.searchsorted(tbs_full, seg_start_t, side='left'))

        # 计算需要去掉的点数（对应Ret长度）
        dt = tbs_full[1] - tbs_full[0] if len(tbs_full) > 1 else tbs_full[0]
        ext_pts = int(np.ceil(ext_time / dt))

        end_idx = min(start_idx + ext_pts, len(tbs_full))
        if start_idx < end_idx:
            keep[start_idx:end_idx] = False

    # 应用掩码得到最终轨迹
    x_rotated = x_rotated_full[keep]
    y_rotated = y_rotated_full[keep]
    tbs = tbs_full[keep]
    theta_dynamic = theta_dynamic[keep]

    return x_rotated, y_rotated, tbs, theta_dynamic, traj_type, params, seg_info


