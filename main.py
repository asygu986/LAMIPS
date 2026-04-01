"""
激光辅助加工路径智能规划软件
核心功能：
1. 生成刀具轨迹和激光轨迹
2. 计算温度场（普通算法/等弧长算法）
3. 可视化轨迹和温度场动画
4. 提供坐标输入、参数配置、状态日志等辅助功能
"""

# ============================== 导入模块区 ==============================
# 基础系统模块
# import math
# import traceback
import sys
import warnings
from datetime import datetime
import html

# 数值计算与可视化模块
# import numpy as np
# from matplotlib.animation import FuncAnimation
# import matplotlib.pyplot as plt

# PyQt5 GUI相关模块
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout,
    QWidget, QPushButton, QMessageBox
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, pyqtSlot, QMetaObject, Qt
)

# 项目自定义模块
from ui_coord_dialog import CoordInputDialog  # 坐标输入对话框UI
from uniform_fun import traj_centered, laser_trajectory  # 轨迹相关工具函数
from traj_gen import *  # 轨迹生成核心函数
from ui_main import Ui_MainWindow  # 主窗口UI
from plot_disp import *  # 绘图显示相关函数
# 找到你原有导入disp_plot的位置，新增：
from plot_disp import InteractiveMatplotlibWidget

# ============================== 全局配置 ==============================
# 忽略弃用警告，避免控制台输出干扰
warnings.filterwarnings("ignore", category=DeprecationWarning)


# ============================== 热轨迹计算线程类 ==============================
class HeatTrajThread(QThread):# 继承QObject/QThread（必须继承QObject才支持信号
    """
    热轨迹计算线程（后台执行，避免阻塞UI）
    功能：根据激光轨迹计算温度场分布，支持普通算法和等弧长算法
    信号说明：
    - finished: 计算完成时发送，携带计算结果（包含温度数据、动画帧等）
    - error: 计算出错时发送，携带错误信息
    - status_update: 状态更新，携带(消息内容, 消息类型)
    - progress_update: 进度更新，携带(进度百分比, 进度描述)
    """
    # 定义信号，定义了一个实例
    finished = pyqtSignal(object)  # 计算完成信号，本质是pyqtSignal类的实例对象
    error = pyqtSignal(str)  # 错误信号
    status_update = pyqtSignal(str, str)  # 状态更新信号 (消息, 类型)
    progress_update = pyqtSignal(float, str)  # 进度更新信号 (百分比, 描述)

    def __init__(self, params, traj_params, con, is_even=True ,x_laser=None, y_laser=None):
        """
        初始化热轨迹计算线程
        参数：
        - params: 公共参数字典（包含材料属性、激光参数等）
        - traj_params: 轨迹参数（轨迹类型、正弦/锯齿波参数等）
        - con: 配置数组（传递给轨迹生成函数）
        - is_even: 是否使用等弧长算法（True=等弧长，False=普通算法）
        """
        super().__init__()

        # 输入参数保存
        self.params = params
        self.traj_params = traj_params
        self.con = con
        self.is_even=is_even

        # 动画相关配置
        self.save_animation = True  # 是否保存动画帧
        self.animation_frames = []  # 存储温度场动画帧（二维切片）
        self.animation_frame_times = []  # 存储每个动画帧对应的时间

        # 外来激光坐标
        # 新增：保存传入的激光轨迹（不再自行计算）
        self.x_laser = x_laser
        self.y_laser = y_laser

    def run(self):
        """
        线程执行入口（自动调用）
        执行流程：
        1. 初始化计算参数
        2. 生成激光/刀具轨迹
        3. 根据算法类型计算温度场(可以修改成普通算法和智能“优化”算法）
        4. 收集动画帧数据
        5. 发送计算结果
        """
        try:
            # 步骤1：发送计算开始状态
            self.status_update.emit(f"开始计算温度场，使用等弧长采样算法", "info")

            # 步骤2：初始化离散化参数（温度场计算的网格配置）
            # 网格尺寸（x/y/z方向的网格数）
            nx, ny, nz = 300, 300, 25
            # 物理尺寸（米）：计算区域的实际大小
            Lx, Ly, Lz = 0.05, 0.05, 0.005
            # 网格步长（米/格）
            dx, dy, dz = Lx / (nx - 1), Ly / (ny - 1), Lz / (nz - 1)
            # 时间步长（秒）- 普通算法使用，对于等弧长采样算法使用计算的dt_max_stable来保持稳定，等下可以删除
            dt = 0.0002
            # 初始化温度场（300K，室温）
            T = np.ones((nx, ny, nz)) * 300

            # 轨迹坐标（暂不中心化，使用原始旋转后坐标）
            x_traj_centered, y_traj_centered = self.x_laser, self.y_laser

            # 步骤4：初始化温度场计算的基础变量
            nt = len(x_traj_centered)  # 时间步数（轨迹点数量），为了显示最后一刻的温度场，所以要以轨迹点数量为nt，总时长为dt*nt
            # 生成刀具轨迹和激光轨迹画布大小

            # 生成网格坐标数组，温度场范围
            x = np.linspace(-0.01, Lx, nx)
            y = np.linspace(-0.01, Ly, ny)
            z = np.linspace(-Lz / 2, Lz / 2, nz)
            # 热扩散系数 (α = k/(ρ·cp))
            alpha = self.params['k'] / (self.params['cp'] * self.params['rho'])

            # 步骤5：定义高斯热源函数（激光热源模型）
            def gaussian_heat_source(P, r, x, y, z, x_center, y_center, z_center, source_radius):
                """
                高斯分布热源模型
                参数：
                - P: 激光功率 (W)
                - r: 热源特征半径 (m)
                - x/y/z: 网格坐标数组
                - x_center/y_center/z_center: 热源中心位置
                - source_radius: 热源有效半径 (m)
                返回：热源强度分布数组
                """
                x_grid, y_grid, z_grid = np.meshgrid(x, y, z, indexing='ij')
                return (P / ((2 * np.pi * r ** 2) ** 1.5)) * np.exp(
                    -((x_grid - x_center) ** 2 +
                      (y_grid - y_center) ** 2 +
                      (z_grid - z[z_center]) ** 2) / (2 * r ** 2)
                )

            # 步骤6：配置计算过程的辅助参数
            self.status_update.emit(f"开始计算温度场，总共 {nt} 个时间步...", "info")
            progress_interval = max(1, nt // 20)  # 进度更新间隔（每5%更新一次）
            animation_interval = max(1, nt // 50)  # 动画帧采集间隔（最多50帧，就是50个步长）

            # 初始化动画帧存储
            self.animation_frames = []
            self.animation_frame_times = []
            # 保存初始状态帧
            if self.save_animation:
                self.animation_frames.append(T[:, :, nz // 2].copy())
                self.animation_frame_times.append(0.0)

            # 步骤7：等弧长计算温度场
            if self.is_even:
                self._calculate_even_arc_length(
                    T, x, y, z, alpha, dx, dy, dz,
                    x_traj_centered, y_traj_centered,
                    nt, progress_interval, animation_interval,
                    gaussian_heat_source
                )


            # 步骤8：封装并发送计算结果，为了在主界面上显示最后一刻温度场和温度场变化动画
            result = {
                'x': x,  # x方向网格坐标
                'y': y,  # y方向网格坐标
                'nz': nz,  # z方向网格数
                'T': T,  # 最终温度场数据
                'traj_type': "line",  # 轨迹类型
                'method': 'even' ,  # 温度计算方法
                'animation_frames': self.animation_frames if self.save_animation else None, # 保存的动画帧，显示动画
                'animation_frame_times': self.animation_frame_times if self.save_animation else None
            }
            self.finished.emit(result)

        except Exception as e:
            # 捕获异常并发送错误信号
            self.error.emit(f"计算错误: {e}")
            traceback.print_exc()

    def _calculate_even_arc_length(self, T, x, y, z, alpha, dx, dy, dz,
                                   x_traj, y_traj, nt, progress_interval,
                                   animation_interval, heat_source_func):
        """
        原始等弧长算法计算温度场（目的是为了保证激光移动速度恒定）
        参数：
        - T: 温度场数组
        - x/y/z: 网格坐标数组
        - alpha: 热扩散系数
        - dx/dy/dz: 网格步长
        - x_traj/y_traj: 轨迹坐标
        - nt: 时间步数
        - progress_interval: 进度更新间隔
        - animation_interval: 动画帧采集间隔
        - heat_source_func: 热源函数
        """
        # 激光扫描速度（米/秒）,这里先固定为2m/s
        v = 2

        # 计算稳定条件下的最大时间步长，这里先固定为1/6
        C = 1 / 6.0
        sum_inv_d2 = (1 / dx ** 2 + 1 / dy ** 2 + 1 / dz ** 2)
        dt_max_stable = C / (alpha * sum_inv_d2)
        self.status_update.emit(f"理论上为保证扩散稳定，dt 需 <= {dt_max_stable:.6g} s", "info")

        # 计算每段轨迹的距离和对应的时间步长
        ds = []
        for i in range(1, nt): # 计算原始轨迹累计弧长
            dist_i = np.sqrt((x_traj[i] - x_traj[i - 1]) ** 2 + (y_traj[i] - y_traj[i - 1]) ** 2)
            ds.append(dist_i)
        ds = np.array(ds)
        dt_array = ds / v  # 每段的时间步长

        # 计算每段需要的子步数（保证稳定性）
        M_list = []
        for dt_i in dt_array:
            M_i = 1 if dt_i <= dt_max_stable else math.ceil(dt_i / dt_max_stable) # 保证时间步长均在dt_max_stable内
            M_list.append(M_i)

        # 逐段计算温度场
        current_time = 0.0
        for t in range(1, nt):
            dt_i = dt_array[t - 1]
            M_i = M_list[t - 1]
            sub_dt = dt_i / M_i  # 子时间步长

            # 子步迭代（保证数值稳定性）
            for m in range(M_i):
                frac = (m + 1) / M_i # 生成等间隔目标弧长
                # 反插值得到等弧长采样各热源中心位置
                x_center = x_traj[t - 1] + frac * (x_traj[t] - x_traj[t - 1])
                y_center = y_traj[t - 1] + frac * (y_traj[t] - y_traj[t - 1])
                z_center = len(z) // 2  # z方向中间层

                # 计算热源分布
                q = heat_source_func(
                    self.params['source_power'], self.params['rb0'],
                    x, y, z, x_center, y_center, z_center, self.params['rb0']
                )

                # 更新温度场（热传导方程）
                T[1:-1, 1:-1, 1:-1] += (
                        alpha * sub_dt * (
                        (T[2:, 1:-1, 1:-1] - 2 * T[1:-1, 1:-1, 1:-1] + T[:-2, 1:-1, 1:-1]) / dx ** 2 +
                        (T[1:-1, 2:, 1:-1] - 2 * T[1:-1, 1:-1, 1:-1] + T[1:-1, :-2, 1:-1]) / dy ** 2 +
                        (T[1:-1, 1:-1, 2:] - 2 * T[1:-1, 1:-1, 1:-1] + T[1:-1, 1:-1, :-2]) / dz ** 2
                ) + sub_dt * q[1:-1, 1:-1, 1:-1] / (self.params['rho'] * self.params['cp'])
                )

            # 更新时间
            current_time += dt_i

            # 采集动画帧
            if self.save_animation and t % animation_interval == 0:
                self.animation_frames.append(T[:, :, len(z) // 2].copy())
                self.animation_frame_times.append(current_time)

            # 更新进度
            if t % progress_interval == 0:
                progress = t / (nt - 1) * 100
                self.progress_update.emit(
                    progress, f"正在计算温度场... 进度: {progress:.0f}% ({t}/{nt - 1}段)"
                )

        # 保存最后一帧
        if self.save_animation:
            self.animation_frames.append(T[:, :, len(z) // 2].copy())
            self.animation_frame_times.append(current_time)

        self.status_update.emit("温度场计算完成！", "success")

    # def _calculate_normal(self, T, x, y, z, alpha, dx, dy, dz, dt,
    #                       x_traj, y_traj, nt, progress_interval,
    #                       animation_interval, heat_source_func):
    #     """
    #     智能优化算法计算温度场（固定时间步长）
    #     参数同等弧长算法，新增dt参数（固定时间步长）
    #     """
    #     current_time = 0.0
    #     for t in range(1, nt):
    #         # 获取当前热源中心位置
    #         x_center, y_center, z_center = laser_trajectory(t, x_traj, y_traj, len(z))
    #
    #         # 计算热源分布
    #         q = heat_source_func(
    #             self.params['source_power'], self.params['rb0'],
    #             x, y, z, x_center, y_center, z_center, self.params['rb0']
    #         )
    #
    #         # 更新温度场（热传导方程）
    #         T[1:-1, 1:-1, 1:-1] += (
    #                 alpha * dt * (
    #                 (T[2:, 1:-1, 1:-1] - 2 * T[1:-1, 1:-1, 1:-1] + T[:-2, 1:-1, 1:-1]) / dx ** 2 +
    #                 (T[1:-1, 2:, 1:-1] - 2 * T[1:-1, 1:-1, 1:-1] + T[1:-1, :-2, 1:-1]) / dy ** 2 +
    #                 (T[1:-1, 1:-1, 2:] - 2 * T[1:-1, 1:-1, 1:-1] + T[1:-1, 1:-1, :-2]) / dz ** 2
    #         ) + dt * q[1:-1, 1:-1, 1:-1] / (self.params['rho'] * self.params['cp'])
    #         )
    #
    #         # 更新时间
    #         current_time += dt
    #
    #         # 采集动画帧
    #         if self.save_animation and t % animation_interval == 0:
    #             self.animation_frames.append(T[:, :, len(z) // 2].copy())
    #             self.animation_frame_times.append(current_time)
    #
    #         # 更新进度
    #         if t % progress_interval == 0:
    #             progress = t / nt * 100
    #             self.progress_update.emit(
    #                 progress, f"正在计算温度场... 进度: {progress:.0f}% ({t}/{nt}步)"
    #             )
    #
    #     # 保存最后一帧
    #     if self.save_animation:
    #         self.animation_frames.append(T[:, :, len(z) // 2].copy())
    #         self.animation_frame_times.append(current_time)
    #
    #     self.status_update.emit("温度场计算完成！", "success")


# ============================== 主窗口类 ==============================
class MyWindow(QMainWindow, Ui_MainWindow):
    """
    主窗口类（程序核心UI逻辑）
    功能模块：
    1. 界面初始化与配置
    2. 状态消息管理
    3. 坐标输入与管理
    4. 参数配置与获取
    5. 轨迹生成（刀具/激光）
    6. 温度场计算（等弧长/智能优化算法）
    7. 动画控制
    """

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 1. 初始化UI界面
        self.setupUi(self)
        self.setWindowTitle("激光辅助加工路径智能规划软件")

        # 2. 初始化数据存储
        self.coordinates = []  # 当前坐标点列表
        self.saved_coordinates = []  # 保存的坐标点列表
        self.last_coordinates = []  # 历史坐标点列表（兼容旧逻辑）

        # 3. 初始化线程与动画相关属性
        self.heat_thread = None  # 热轨迹计算线程
        self.heat_animation_timer = None  # 动画定时器
        self.heat_animation_canvas = None  # 动画画布
        self.heat_animation_controller = None  # 动画控制器

        # 4. 绑定UI控件事件,也是定义的函数
        self._bind_ui_events()

        # 5. 初始化默认配置,这些函数都是下面定义的
        self.set_default_values()  # 设置默认参数
        self.init_status_frame()  # 初始化状态显示区
        self.disable_animation_buttons()  # 初始禁用动画按钮
        # 定义刀具和激光轨迹x，y画布范围
        Lx, Ly, Lz = 0.05, 0.05, 0.005
        self.x_scope = [-0.01, Lx]
        self.y_scope = [-0.01, Ly]
        # 定义激光轨迹点
        self.x_laser=[]
        self.y_laser=[]

        # 6.新增：初始化交互式绘图控件（替代原有的QLabel）,实际上你在UI文件里面创建后就不用重复设了
        # self.cutter_plot_widget = InteractiveMatplotlibWidget()
        # self.laser_plot_widget = InteractiveMatplotlibWidget()

    # ========================== UI事件绑定 ==========================
    def _bind_ui_events(self):
        """绑定所有UI控件和相应事件处理函数"""
        # 轨迹生成按钮
        self.btn_cutter.clicked.connect(self.cutter_traj_gen)  # 按下按钮后，执行生成刀具轨迹的函数
        self.btn_laser.clicked.connect(self.laser_traj_gen)  # 生成激光轨迹

        # 温度场计算按钮,
        self.btn_heat_even.clicked.connect(self.heat_traj_gen_even)  # 等弧长算法
        # 激光轨迹智能优化按钮
        # self.btn_opt_laser.clicked.connect(self.heat_traj_gen)  # 智能优化激光轨迹

        # 坐标输入按钮
        self.btn_open_coords.clicked.connect(self.open_coord_dialog)  # 打开坐标对话框

        # 轨迹类型选择框
        self.comboBox_trajectory_type.setCurrentIndex(0)
        self.stackedWidget_params.setCurrentIndex(0)
        self.comboBox_trajectory_type.currentIndexChanged.connect(self.get_trajectory_parameters)

        # 动画控制按钮（后续动态绑定）
        self.connect_animation_buttons()



    # ========================== 状态消息管理 ==========================
    def init_status_frame(self):
        """初始化状态显示区域（日志输出）"""
        # 配置状态文本框
        self.textEdit_status.setReadOnly(True)
        self.textEdit_status.setAcceptRichText(True)  # 支持富文本（彩色消息）

        # 绑定状态管理按钮
        if hasattr(self, 'btn_clear_status'):
            self.btn_clear_status.clicked.connect(self.clear_status_messages)
        if hasattr(self, 'btn_save_log'):
            self.btn_save_log.clicked.connect(self.save_status_log)

        # 显示启动信息
        self.append_status_message("应用程序已启动", "info")

    def append_status_message(self, message, message_type="info"):
        """
        向状态区添加带颜色的消息
        参数：
        - message: 消息内容
        - message_type: 消息类型（info/warning/error/success）
        """
        # 时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 消息样式配置
        style_config = {
            "info": {"color": "#333333", "prefix": "[INFO]"},  # 深灰色
            "warning": {"color": "#ff9900", "prefix": "[WARN]"},  # 橙色
            "error": {"color": "#ff0000", "prefix": "[ERROR]"},  # 红色
            "success": {"color": "#009900", "prefix": "[SUCCESS]"}  # 绿色
        }
        config = style_config.get(message_type, style_config["info"])

        # 转义HTML特殊字符，避免格式错误
        safe_message = html.escape(message)

        # 生成富文本消息
        html_msg = f'<span style="color:{config["color"]};">[{timestamp}] <b>{config["prefix"]}</b> {safe_message}</span><br>'

        # 显示消息
        self.textEdit_status.append(html_msg)

        # 自动滚动到底部
        if hasattr(self, 'checkBox_auto_scroll') and self.checkBox_auto_scroll.isChecked():
            scrollbar = self.textEdit_status.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        # 控制台同步输出
        print(f"[{timestamp}] {config['prefix']} {message}")

    def show_status_message(self, message, message_type="info"):
        """
        显示状态消息（封装版，支持状态栏提示）
        参数同append_status_message
        """
        # 输出到状态文本框
        self.append_status_message(message, message_type)

        # 状态栏短消息提示（3秒后消失）
        if hasattr(self, 'statusbar'):
            brief_msg = message[:50] + "..." if len(message) > 50 else message
            self.statusbar.showMessage(brief_msg, 3000)

    def clear_status_messages(self):
        """清空所有状态消息"""
        self.textEdit_status.clear()
        self.append_status_message("状态信息已清空", "info")

    def save_status_log(self):
        """保存状态日志到文件"""
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"状态日志_{timestamp}.txt"

        # 选择保存路径
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存状态日志", default_filename, "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if filepath:
            try:
                # 保存日志内容
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.textEdit_status.toPlainText())
                self.append_status_message(f"状态日志已保存到: {filepath}", "success")
            except Exception as e:
                self.append_status_message(f"保存日志失败: {e}", "error")

    # ========================== 参数配置管理 ==========================
    def set_default_values(self):
        """为所有输入框设置默认参数值"""
        try:
            # 默认参数字典（键：控件名，值：默认值）
            default_params = {
                "lineEdit_Det": "10e-3",  # 刀具直径 (m)
                "lineEdit_ae": "7.5e-3",  # 切削宽度 (m)
                "lineEdit_ap": "-0.26e-3",  # 切削深度 (m)
                "lineEdit_nC": "474/60",  # 主轴转速 (r/s)
                "lineEdit_fz": "0.5e-3",  # 每齿进给量 (m)
                "lineEdit_k": "15",  # 热传导系数 (W/(m·K))
                "lineEdit_rho": "7800",  # 材料密度 (kg/m³)
                "lineEdit_cp": "500",  # 比热容 (J/(kg·K))
                "lineEdit_source_power": "2000",  # 激光功率 (W)
                "lineEdit_rb0": "1e-3",  # 激光光斑半径 (m)
                "lineEdit_N": "8"  # 轨迹采样数
            }

            # 设置默认值
            for widget_name, value in default_params.items():
                getattr(self, widget_name).setText(value)

            self.show_status_message("已为所有输入框设置默认值", "success")
        except Exception as e:
            self.show_status_message(f"设置默认值时出错: {e}", "error")

    def get_trajectory_parameters(self):
        """根据选择的轨迹类型切换参数配置页面并设置默认值"""
        traj_type = self.comboBox_trajectory_type.currentText()

        # 切换参数配置页面
        page_index = {"line": 0, "sin": 1, "zigzag": 2}.get(traj_type, 0)
        self.stackedWidget_params.setCurrentIndex(page_index)

        # 轨迹类型默认参数
        traj_defaults = {
            "sin": [
                ("lineEdit_sinAmplitude", "0.01"),  # 正弦轨迹振幅 (m)
                ("lineEdit_sinFrequency", "1.5")  # 正弦轨迹频率 (Hz)
            ],
            "zigzag": [
                ("lineEdit_num_zigzags", "3"),  # 锯齿波数量
                ("lineEdit_period", "6.28"),  # 锯齿波周期
                ("lineEdit_amplitude_zigzag", "0.009"),  # 锯齿波振幅 (m)
                ("lineEdit_offset", "0.011")  # 锯齿波偏移 (m)
            ]
        }

        # 设置轨迹类型默认参数
        for widget_name, value in traj_defaults.get(traj_type, []):
            if not getattr(self, widget_name).text():
                getattr(self, widget_name).setText(value)

    def get_current_trajectory_params(self):
        """获取当前选择的轨迹类型及在Qwidget输入的参数，用于计算轨迹和温度场"""
        traj_type = self.comboBox_trajectory_type.currentText()
        traj_params = {"trajectory_type": traj_type, "params": {}}

        try:
            # 根据轨迹类型获取参数
            if traj_type == "sin":
                traj_params["params"] = {
                    "amplitude": float(self.lineEdit_sinAmplitude.text()),
                    "frequency": float(self.lineEdit_sinFrequency.text())
                }
            elif traj_type == "zigzag":
                traj_params["params"] = {
                    "num_zigzags": int(self.lineEdit_num_zigzags.text()),
                    "amplitude_zigzag": float(self.lineEdit_amplitude_zigzag.text()),
                    "period": float(self.lineEdit_period.text()),
                    "offset": float(self.lineEdit_offset.text())
                }
        except ValueError as e:
            self.show_status_message(f"{traj_type}轨迹参数错误: {e}", "error")

        return traj_params

    def _get_common_parameters(self):
        """提取所有公共参数，包括输入参数（材料、激光、切削参数）和计算得到的参数fx，也是在计算轨迹和温度场时调用"""
        try:
            # 从UI控件读取参数
            Ret = float(self.lineEdit_Det.text()) / 2  # 刀具半径 (m)
            ae = float(self.lineEdit_ae.text())  # 切削宽度 (m)
            ap = float(self.lineEdit_ap.text())  # 切削深度 (m)
            nC = eval(self.lineEdit_nC.text())  # 主轴转速 (r/s)
            fz = float(self.lineEdit_fz.text())  # 每齿进给量 (m)
            k = float(self.lineEdit_k.text())  # 热传导系数 (W/(m·K))
            rho = float(self.lineEdit_rho.text())  # 材料密度 (kg/m³)
            cp = float(self.lineEdit_cp.text())  # 比热容 (J/(kg·K))
            source_power = float(self.lineEdit_source_power.text())  # 激光功率 (W)
            rb0 = eval(self.lineEdit_rb0.text())  # 激光光斑半径 (m)
            N = int(self.lineEdit_N.text())  # 轨迹采样数

            # 计算派生参数
            wC = nC * 2 * np.pi  # 主轴角速度 (rad/s)
            betaC = 2 * np.arcsin(ae / 2 / Ret)  # 切削角 (rad)
            fr = fz * 4  # 进给率 (m/s)
            fx = fr * nC  # X方向进给率 (m/s)
            fy = 0

            # 获取坐标起点
            if self.coordinates:
                X0Cutter = self.coordinates[0][0]
                Y0Cutter = self.coordinates[0][1]
            else:
                X0Cutter = 0.0
                Y0Cutter = 0.0
                self.show_status_message("警告：坐标列表为空，使用默认起点 (0,0)", "warning")

            # 返回参数字典
            return {
                'Ret': Ret, 'ae': ae, 'ap': ap, 'nC': nC, 'fz': fz,
                'k': k, 'rho': rho, 'cp': cp, 'source_power': source_power,
                'rb0': rb0, 'N': N, 'wC': wC, 'betaC': betaC, 'fx': fx, 'fy':fy,
                'X0Cutter': X0Cutter, 'Y0Cutter': Y0Cutter,
                'coordinates': self.coordinates if self.coordinates else [(0.0, 0.0)]
            }
        except ValueError as e:
            raise ValueError(f"参数转换错误: {e}")
        except Exception as e:
            raise Exception(f"获取参数时出错: {e}")

    def _get_con_array(self, params):
        """构建轨迹生成函数所需的配置数组"""
        # 激光起点X坐标（相对于刀具偏移5.5mm），这个偏移量也是可以修改的
        bias = 5.5e-3
        X0Laser = params['X0Cutter'] + bias

        # 配置数组（各元素含义见轨迹生成函数文档）
        return [
            2, params['ae'], params['ap'], params['k'],
            params['k'] / (params['cp'] * params['rho']),  # 热扩散系数 alpha
            params['Ret'], params['Ret'], params['rb0'], params['betaC'], 50,  # beta_b = 50
            params['X0Cutter'], params['Y0Cutter'],  # 刀具起点坐标
            X0Laser, params['Y0Cutter'],  # 激光起点坐标
            4, params['fx'], params['fy'], params['wC'],  # insertNr, fx, fy, wC # 这里设定 fy=0
            2, 5.5e-3,  # parallNr, bias
            4000, 50, 40, 1, 12,  # intPointNr, nodesNrX/Y/Z, memAvailableGB(仿真参数）
            100, 1, 0.5, params['coordinates']  # pointOfOnePass(一段刀具轨迹对应激光扫描的点数）, base_factor, sharpness_factor（这个是角度因子修正曲率）, coordinates
        ]

    # ========================== 坐标管理 ==========================
    def open_coord_dialog(self):
        """打开坐标输入对话框，允许用户输入/编辑轨迹坐标点"""
        try:
            # 创建坐标对话框
            dialog = CoordInputDialog(self)

            # 传递已保存的坐标点
            coords_to_pass = []
            if self.saved_coordinates:
                coords_to_pass = self.saved_coordinates
            elif self.last_coordinates:
                coords_to_pass = self.last_coordinates

            if coords_to_pass:
                self.show_status_message(f"传递 {len(coords_to_pass)} 个坐标到对话框", "info")
                dialog.set_coordinates(coords_to_pass)
            else: # 最开始打开时会输出一次
                self.show_status_message("没有保存的坐标，对话框将显示空表格", "info")

            # 显示对话框并处理结果
            if dialog.exec_():
                new_coords = dialog.get_coordinates()
                self.show_status_message(f"从对话框获取到 {len(new_coords)} 个坐标", "info")

                if new_coords:
                    # 更新坐标存储,此时类变量coordinates已经有了值
                    self.coordinates = new_coords
                    self.saved_coordinates = new_coords.copy()
                    self.last_coordinates = new_coords.copy()

                    # 显示坐标点信息
                    for i, (x, y) in enumerate(new_coords):
                        self.show_status_message(f"点{i + 1}: ({x:.6f}, {y:.6f})", "info")
                else:
                    self.show_status_message("没有输入有效坐标", "info")

        except Exception as e:
            self.show_status_message(f"打开坐标对话框时出错: {e}", "error")
            traceback.print_exc()

# 真正执行计算部分
    # ========================== 轨迹生成 ==========================
    def cutter_traj_gen(self):
        """生成刀具轨迹并显示"""
        try:
            # 1. 获取参数
            common_params = self._get_common_parameters() # 坐标框输入参数
            traj_params = self.get_current_trajectory_params()  # 主要是轨迹选框中输入的变量（不是坐标）
            con_array = self._get_con_array(common_params)  # 其他计算得到变量

            # 2. 检查坐标点数量（至少2个）,没有两个时会自动绘制一个矩形路径
            if len(self.coordinates) < 2:
                self.show_status_message("警告：需要至少两个点，使用默认矩形路径", "warning")
                # 生成默认矩形路径
                start_x = common_params['X0Cutter']
                start_y = common_params['Y0Cutter']
                self.coordinates = [
                    (start_x, start_y),
                    (start_x + 0.02, start_y),
                    (start_x + 0.02, start_y + 0.01),
                    (start_x, start_y + 0.01),
                    (start_x, start_y)  # 闭合路径
                ]

            # 3. 显示坐标点信息
            self.show_status_message(f"生成多段轨迹，共{len(self.coordinates)}个点", "info")
            for i, (x, y) in enumerate(self.coordinates):
                self.show_status_message(f"点{i + 1}: ({x:.6f}, {y:.6f})", "info")

            # 4. 生成刀具轨迹数据
            (x_rotated, y_rotated, tbs, theta_dynamic,
             cutter_traj_type, params_traj, seg_info) = sweeping_laser_trajectory_with_distance_preservation(
                common_params['ae'] + 2 * common_params['rb0'],
                con_array, common_params['N'], traj_params, common_params['coordinates']
            )

            # 5. 获取刀具轨迹坐标
            x_cutter, y_cutter, _ = cutter_trajectory(
                tbs, con_array, cutter_traj_type, params_traj, common_params['coordinates']
            )

            # 6. 绘制并显示轨迹
            fig = cutter_matplotlib_plot(x_cutter, y_cutter, common_params['Ret'], cutter_traj_type, self.x_scope, self.y_scope)
            display_plot_on_label(fig, self.cutter_plot_display)

            self.show_status_message("生成刀具轨迹完毕", "success")

        except ValueError as e:
            self.show_status_message(f"参数转换错误: {e}", "error")
        except Exception as e:
            self.show_status_message(f"计算错误: {e}", "error")

    def laser_traj_gen(self):
        """生成激光轨迹并显示"""
        try:
            # 1. 获取参数
            common_params = self._get_common_parameters()
            traj_params = self.get_current_trajectory_params()
            con_array = self._get_con_array(common_params)

            # 2. 生成激光轨迹数据
            (x_rotated, y_rotated, tbs, theta_dynamic,
             cutter_traj_type, params_traj, seg_info) = sweeping_laser_trajectory_with_distance_preservation(
                common_params['ae'] + 2 * common_params['rb0'],
                con_array, common_params['N'], traj_params, common_params['coordinates']
            )

            # 3. 获取刀具轨迹（用于参考显示）
            x_cutter, y_cutter, _ = cutter_trajectory(
                tbs, con_array, cutter_traj_type, params_traj, common_params['coordinates']
            )
            # 将激光参数输入
            self.x_laser=x_rotated
            self.y_laser=y_rotated

            # 4. 绘制并显示动态激光轨迹
            fig = laser_matplotlib_plot(
                x_cutter, y_cutter, common_params['Ret'], common_params['rb0'],
                x_rotated, y_rotated, cutter_traj_type,self.x_scope, self.y_scope
            )

            self.laser_plot_widget.set_figure(fig)
            # display_plot_on_label(fig, self.laser_plot_display)

            self.show_status_message("生成激光轨迹完毕", "success")

        except ValueError as e:
            self.show_status_message(f"参数转换错误: {e}", "error")
        except Exception as e:
            self.show_status_message(f"计算错误: {e}", "error")

    # ========================== 温度场计算 ==========================
    def _setup_heat_thread_connections(self):
        """设置热轨迹计算线程的信号连接"""
        if self.heat_thread:
            self.heat_thread.status_update.connect(self.show_status_message)
            self.heat_thread.progress_update.connect(self._update_progress)
            self.heat_thread.finished.connect(self._on_heat_calculation_finished)
            self.heat_thread.error.connect(self._on_heat_calculation_error)
            self.heat_thread.finished.connect(self.heat_thread.deleteLater)

    def _start_heat_calculation(self, is_even):
        """
        通用的温度场计算启动函数
        参数：
        - is_even: 是否使用等弧长算法
        """
        try:
            # 1. 获取参数
            common_params = self._get_common_parameters()
            traj_params = self.get_current_trajectory_params()
            con_array = self._get_con_array(common_params)

            # 2. 创建并启动计算线程
            self.heat_thread = HeatTrajThread(common_params, traj_params, con_array, is_even, x_laser=self.x_laser, y_laser=self.y_laser)
            self._setup_heat_thread_connections()
            self.heat_thread.start()

            # 3. 禁用计算按钮避免重复点击
            self.btn_heat_even.setEnabled(False)

        except Exception as e:
            self.show_status_message(f"启动热轨迹计算失败: {e}", "error")

# 真正执行计算部分
#     def heat_traj_gen(self):
#         """启动普通算法的温度场计算（多线程）"""
#         self._start_heat_calculation(is_even=False)

    def heat_traj_gen_even(self):
        """启动等弧长算法的温度场计算（多线程）"""
        self._start_heat_calculation(is_even=True)


    @pyqtSlot(float, str)
    def _update_progress(self, progress, message):
        """更新计算进度显示"""
        self.show_status_message(message, "info")
        # 如需进度条，可在此添加：self.progressBar.setValue(int(progress))

    @pyqtSlot(object)
    def _on_heat_calculation_finished(self, result):
        """温度场计算完成后的处理"""
        try:
            # 1. 绘制温度场静态图
            if result['method'] == 'even':
                fig = heat_even_matplotlib_plot(
                    result['x'], result['y'], result['nz'], result['T'], result['traj_type']
                )

            display_plot_on_label(fig, self.heat_plot_display)

            # 2. 处理动画数据
            if result.get('animation_frames') and result.get('animation_frame_times'):
                self.show_status_message("正在创建温度场动画...", "info")

                # 清理旧动画
                if self.heat_animation_controller:
                    self.heat_animation_controller.close()
                    self.heat_animation_controller = None

                # 禁用动画按钮直到创建完成
                self.disable_animation_buttons()

                # 创建新动画控制器
                self.heat_animation_controller = create_simple_heat_animation(
                    self.heat_animation_container,
                    result['x'], result['y'],
                    result['animation_frames'],
                    result['animation_frame_times'],
                    result['traj_type']
                )

                if self.heat_animation_controller:
                    # 重新绑定动画按钮
                    self.connect_animation_buttons()
                    # 启用动画按钮
                    self.enable_animation_buttons()
                    # 更新按钮状态（初始暂停）
                    self.update_animation_button_states(is_playing=False)
                    self.show_status_message("温度场动画已创建完成！", "success")
                else:
                    self.show_status_message("创建动画控制器失败", "warning")
                    self.disable_animation_buttons()

            else:
                # 无动画数据时清空容器
                if self.heat_animation_container.layout():
                    while self.heat_animation_container.layout().count():
                        item = self.heat_animation_container.layout().takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                self.disable_animation_buttons()
                self.show_status_message("没有生成动画数据", "info")

            # 3. 显示完成消息
            method_name = "等弧长采样" if result['method'] == 'even' else ""
            self.show_status_message(f"生成{method_name}温度场二维切片图完毕", "success")

        except Exception as e:
            self.show_status_message(f"图形创建失败: {e}", "error")
            traceback.print_exc()
            self.disable_animation_buttons()
        finally:
            # 重新启用计算按钮
            self.btn_heat_even.setEnabled(True)
            # 清理线程引用
            self.heat_thread = None

    @pyqtSlot(str)
    def _on_heat_calculation_error(self, error_msg):
        """温度场计算出错的处理"""
        self.show_status_message(error_msg, "error")
        # 重新启用计算按钮
        self.btn_heat_even.setEnabled(True)
        # 清理线程引用
        self.heat_thread = None

    # ========================== 动画控制 ==========================
    def connect_animation_buttons(self):
        """绑定动画控制按钮的事件"""
        # 先断开旧连接（避免重复绑定）
        for btn_name in ['btn_anim_play', 'btn_anim_pause', 'btn_anim_reset', 'btn_anim_save']:
            if hasattr(self, btn_name):
                try:
                    getattr(self, btn_name).clicked.disconnect()
                except:
                    pass

        # 绑定新连接
        if hasattr(self, 'btn_anim_play'):
            self.btn_anim_play.clicked.connect(self.on_anim_play)
        if hasattr(self, 'btn_anim_pause'):
            self.btn_anim_pause.clicked.connect(self.on_anim_pause)
        if hasattr(self, 'btn_anim_reset'):
            self.btn_anim_reset.clicked.connect(self.on_anim_reset)
        if hasattr(self, 'btn_anim_save'):
            self.btn_anim_save.clicked.connect(self.on_anim_save)

    def disable_animation_buttons(self):
        """禁用所有动画控制按钮"""
        for btn_name in ['btn_anim_play', 'btn_anim_pause', 'btn_anim_reset', 'btn_anim_save']:
            if hasattr(self, btn_name):
                getattr(self, btn_name).setEnabled(False)

    def enable_animation_buttons(self):
        """启用动画控制按钮"""
        if self.heat_animation_controller:
            if hasattr(self, 'btn_anim_play'):
                self.btn_anim_play.setEnabled(True)
            if hasattr(self, 'btn_anim_pause'):
                self.btn_anim_pause.setEnabled(False)  # 初始暂停状态
            if hasattr(self, 'btn_anim_reset'):
                self.btn_anim_reset.setEnabled(True)
            if hasattr(self, 'btn_anim_save'):
                self.btn_anim_save.setEnabled(True)
        else:
            self.disable_animation_buttons()

    def update_animation_button_states(self, is_playing):
        """更新动画按钮状态（播放/暂停切换）"""
        if self.heat_animation_controller:
            if hasattr(self, 'btn_anim_play'):
                self.btn_anim_play.setEnabled(not is_playing)
            if hasattr(self, 'btn_anim_pause'):
                self.btn_anim_pause.setEnabled(is_playing)

    def on_anim_play(self):
        """播放动画"""
        if self.heat_animation_controller:
            self.heat_animation_controller.play()
            self.update_animation_button_states(is_playing=True)
            self.show_status_message("动画开始播放", "info")
        else:
            self.show_status_message("没有可用的动画数据", "warning")

    def on_anim_pause(self):
        """暂停动画"""
        if self.heat_animation_controller:
            self.heat_animation_controller.pause()
            self.update_animation_button_states(is_playing=False)
            self.show_status_message("动画已暂停", "info")
        else:
            self.show_status_message("没有可用的动画数据", "warning")

    def on_anim_reset(self):
        """重置动画到第一帧"""
        if self.heat_animation_controller:
            self.heat_animation_controller.reset()
            self.update_animation_button_states(is_playing=False)
            self.show_status_message("动画已重置到第一帧", "info")
        else:
            self.show_status_message("没有可用的动画数据", "warning")

    def on_anim_save(self):
        """保存动画到文件"""
        if self.heat_animation_controller:
            if self.heat_animation_controller.save(self):
                self.show_status_message("动画保存成功！", "success")
            else:
                self.show_status_message("动画保存失败", "error")
        else:
            self.show_status_message("没有可用的动画数据", "warning")


# ============================== 程序入口 ==============================
if __name__ == '__main__':
    """程序主入口"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    # 创建主窗口
    main_window = MyWindow()
    # 显示主窗口
    main_window.show()
    # 运行应用程序
    sys.exit(app.exec_())