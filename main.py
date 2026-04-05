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
import sys
import warnings
from datetime import datetime
import html
import time

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
# 为了提升计算速率我进行了如下修改：
# 降低网格分辨率，从300*300*25到100*100*10
# 局部热源添加：不再生成整个网格的高斯分布，而是只计算激光中心周围有效区域（半径 3 倍光斑）内的网格点，大幅减少计算量。
#
# 预计算网格坐标：将 x, y, z 数组存储为实例变量，避免重复传递。
#
# 优化循环：减少不必要的数组拷贝和索引计算。
class HeatTrajThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str, str)
    progress_update = pyqtSignal(float, str)

    def __init__(self, con_array, common_params, traj_params, is_even=False, x_laser=None, y_laser=None,
                 vLaser=0, nt_fit_cutter=0):
        super().__init__()
        self.con = con_array
        self.params = common_params
        self.traj_params = traj_params
        self.is_even = is_even
        self.save_animation = True
        self.animation_frames = []
        self.animation_frame_times = []
        self.x_laser = x_laser
        self.y_laser = y_laser
        self.vLaser = vLaser
        self.nt_fitting= nt_fit_cutter

    def run(self):
        try:
            self.status_update.emit("开始计算温度场", "info")

            # 网格参数（已降低分辨率以加速）
            nx, ny, nz = 200, 200, 10
            Lx, Ly, Lz = 0.1, 0.1, 0.005
            dx, dy, dz = Lx / (nx - 1), Ly / (ny - 1), Lz / (nz - 1)
            T = np.ones((nx, ny, nz)) * 300
            x_traj_centered, y_traj_centered = self.x_laser, self.y_laser
            nt = len(x_traj_centered)
            # print("相配合时间点数:",self.nt_fitting)
            dt = self.con["dt"] * self.nt_fitting / nt
            # print(f"轨迹点数: {nt}")

            # 网格坐标（用于局部热源添加）
            x = np.linspace(-0.02, Lx, nx)
            y = np.linspace(-0.02, Ly, ny)
            z = np.linspace(-Lz / 2, Lz / 2, nz)

            alpha = self.params['k'] / (self.params['cp'] * self.params['rho'])
            vLaser = self.vLaser

            # 预计算激光参数
            P = self.params['laser_p']
            r = self.params['laser_r']
            rho_cp = self.params['rho'] * self.params['cp']
            # print(f"开始计算温度场，总共 {nt} 个时间步，共计 {nt*dt:.2f} s")
            self.status_update.emit(f"开始计算温度场，共计 {nt*dt:.2f} s", "info")
            progress_interval = max(1, nt // 20)
            animation_interval = max(1, nt // 50)

            self.animation_frames = []
            self.animation_frame_times = []
            if self.save_animation:
                self.animation_frames.append(T[:, :, nz // 2].copy())
                self.animation_frame_times.append(0.0)

            if self.is_even:
                self._calculate_even_arc_length(
                    T, x, y, z, dt, dx, dy, dz, alpha,
                    x_traj_centered, y_traj_centered, nt,
                    P, r, rho_cp, vLaser,
                    progress_interval, animation_interval
                )

            else:
                self._calculate_normal(
                    T, x, y, z, dt, dx, dy, dz, alpha,
                    x_traj_centered, y_traj_centered, nt,
                    P, r, rho_cp,
                    progress_interval, animation_interval
                )

            result = {
                'x': x, 'y': y, 'nz': nz, 'T': T, 'traj_type': "line",
                'method': 'even' if self.is_even==True else "normal",
                'animation_frames': self.animation_frames if self.save_animation else None,
                'animation_frame_times': self.animation_frame_times if self.save_animation else None
            }
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"计算错误: {e}")
            traceback.print_exc()

    def _calculate_even_arc_length(self, T, x, y, z, dt, dx, dy, dz, alpha,
                                   x_traj, y_traj, nt, P, r, rho_cp, vLaser,
                                   progress_interval, animation_interval):
        """等弧长算法 - 使用局部热源添加优化"""
        v = vLaser
        C = 1 / 6.0
        sum_inv_d2 = (1/dx**2 + 1/dy**2 + 1/dz**2)
        dt_max_stable = C / (alpha * sum_inv_d2)
        self.status_update.emit(f"稳定时间步长上限: {dt_max_stable:.6g} s", "info")

        # 计算每段距离和实际时间步长
        ds = np.sqrt(np.diff(x_traj)**2 + np.diff(y_traj)**2)
        dt_array = ds / v
        if dt_max_stable>dt:
            dt_max_stable=dt

        M_list = np.maximum(1, np.ceil(dt_array / dt_max_stable)).astype(int)

        total_segments = nt - 1
        current_time = 0.0

        # 预计算网格范围和步长（用于局部热源索引）
        nx, ny, nz = T.shape
        x_min, x_max = x[0], x[-1]
        y_min, y_max = y[0], y[-1]
        z_mid = nz // 2

        # 热源有效半径（3倍光斑半径）
        r_eff = 3 * r
        # 预计算高斯归一化系数
        norm_factor = P / ((2 * np.pi * r**2) ** 1.5)

        # 进度更新间隔（每 2% 更新一次）
        progress_step = max(1, total_segments // 50)
        anim_step = max(1, total_segments // 50)   # 最多 50 帧动画

        for idx in range(total_segments):
            # 定期让出 CPU，使 UI 有机会响应
            if idx % 100 == 0:
                self.msleep(1)

            dt_i = dt_array[idx]
            M_i = M_list[idx]
            sub_dt = dt_i / M_i

            # 当前段起点和终点坐标
            x0, x1 = x_traj[idx], x_traj[idx+1]
            y0, y1 = y_traj[idx], y_traj[idx+1]

            for m in range(M_i):
                frac = (m + 1) / M_i
                xc = x0 + frac * (x1 - x0)
                yc = y0 + frac * (y1 - y0)
                zc = z_mid

                # ----- 热传导扩散更新（向量化）-----
                T[1:-1, 1:-1, 1:-1] += alpha * sub_dt * (
                    (T[2:, 1:-1, 1:-1] - 2*T[1:-1, 1:-1, 1:-1] + T[:-2, 1:-1, 1:-1]) / dx**2 +
                    (T[1:-1, 2:, 1:-1] - 2*T[1:-1, 1:-1, 1:-1] + T[1:-1, :-2, 1:-1]) / dy**2 +
                    (T[1:-1, 1:-1, 2:] - 2*T[1:-1, 1:-1, 1:-1] + T[1:-1, 1:-1, :-2]) / dz**2
                )

                # ----- 局部高斯热源添加（优化核心）-----
                # 确定影响范围在网格上的索引边界
                ix_min = max(0, int(np.searchsorted(x, xc - r_eff)) - 1)
                ix_max = min(nx, int(np.searchsorted(x, xc + r_eff)) + 1)
                iy_min = max(0, int(np.searchsorted(y, yc - r_eff)) - 1)
                iy_max = min(ny, int(np.searchsorted(y, yc + r_eff)) + 1)
                # z方向只考虑中间层附近（因为z范围很小，且热源集中在中间）
                iz_min = max(0, zc - 2)
                iz_max = min(nz, zc + 3)

                # 提取子网格坐标
                x_sub = x[ix_min:ix_max]
                y_sub = y[iy_min:iy_max]
                z_sub = z[iz_min:iz_max]
                # 计算子网格上各点到热源中心的距离平方
                X, Y, Z = np.meshgrid(x_sub, y_sub, z_sub, indexing='ij')
                dist2 = (X - xc)**2 + (Y - yc)**2 + (Z - z[zc])**2
                # 计算高斯热源值（只对有效半径内）
                q_sub = norm_factor * np.exp(-dist2 / (2 * r**2))
                # 加到温度场的对应子区域
                T[ix_min:ix_max, iy_min:iy_max, iz_min:iz_max] += sub_dt * q_sub / rho_cp

            current_time += dt_i

            # 采集动画帧（限制最大帧数 100）
            if self.save_animation and idx % anim_step == 0 and len(self.animation_frames) < 100:
                self.animation_frames.append(T[:, :, nz // 2].copy())
                self.animation_frame_times.append(current_time)

            # 更新进度
            if idx % progress_step == 0:
                progress = (idx + 1) / total_segments * 100
                # print(progress, f"计算温度场... {progress:.0f}% ({idx + 1}/{total_segments})")
                self.progress_update.emit(progress, f"计算温度场... {progress:.0f}% ")

        # 保存最后一帧
        if self.save_animation and len(self.animation_frames) < 100:
            self.animation_frames.append(T[:, :, nz // 2].copy())
            self.animation_frame_times.append(current_time)

        self.status_update.emit("温度场计算完成！", "success")

    def _calculate_normal(self, T, x, y, z, dt, dx, dy, dz, alpha,
                                   x_traj, y_traj, nt, P, r, rho_cp,
                                   progress_interval, animation_interval):
        """固定时间步长算法 - 每个轨迹点对应一个 dt，不依赖弧长"""
        C = 1 / 6.0
        sum_inv_d2 = (1 / dx ** 2 + 1 / dy ** 2 + 1 / dz ** 2)
        dt_max_stable = C / (alpha * sum_inv_d2)
        self.status_update.emit(f"稳定时间步长上限: {dt_max_stable:.6g} s", "info")

        # 确保 dt 不大于稳定上限，否则拆分子步
        if dt <= dt_max_stable:
            M = 1
            sub_dt = dt
        else:
            M = int(np.ceil(dt / dt_max_stable))
            sub_dt = dt / M
            self.status_update.emit(f"dt={dt:.6g}s 超过稳定上限，将每个步长拆分为 {M} 个子步", "info")

        total_steps = nt  # 共有 nt 个轨迹点（每个点对应一个时间步）
        current_time = 0.0

        # 预计算网格参数
        nx, ny, nz = T.shape
        z_mid = nz // 2
        r_eff = 3 * r
        norm_factor = P / ((2 * np.pi * r ** 2) ** 1.5)

        progress_step = max(1, total_steps // 50)
        anim_step = max(1, total_steps // 50)

        for idx in range(total_steps):
            # 定期让出 CPU
            if idx % 100 == 0:
                self.msleep(1)

            # 当前热源中心位置（直接使用轨迹点）
            xc = x_traj[idx]
            yc = y_traj[idx]
            zc = z_mid

            # 将一个时间步 dt 拆分为 M 个子步
            for _ in range(M):
                # 热传导扩散更新
                T[1:-1, 1:-1, 1:-1] += alpha * sub_dt * (
                        (T[2:, 1:-1, 1:-1] - 2 * T[1:-1, 1:-1, 1:-1] + T[:-2, 1:-1, 1:-1]) / dx ** 2 +
                        (T[1:-1, 2:, 1:-1] - 2 * T[1:-1, 1:-1, 1:-1] + T[1:-1, :-2, 1:-1]) / dy ** 2 +
                        (T[1:-1, 1:-1, 2:] - 2 * T[1:-1, 1:-1, 1:-1] + T[1:-1, 1:-1, :-2]) / dz ** 2
                )

                # 局部高斯热源添加
                ix_min = max(0, int(np.searchsorted(x, xc - r_eff)) - 1)
                ix_max = min(nx, int(np.searchsorted(x, xc + r_eff)) + 1)
                iy_min = max(0, int(np.searchsorted(y, yc - r_eff)) - 1)
                iy_max = min(ny, int(np.searchsorted(y, yc + r_eff)) + 1)
                iz_min = max(0, zc - 2)
                iz_max = min(nz, zc + 3)

                x_sub = x[ix_min:ix_max]
                y_sub = y[iy_min:iy_max]
                z_sub = z[iz_min:iz_max]
                X, Y, Z = np.meshgrid(x_sub, y_sub, z_sub, indexing='ij')
                dist2 = (X - xc) ** 2 + (Y - yc) ** 2 + (Z - z[zc]) ** 2
                q_sub = norm_factor * np.exp(-dist2 / (2 * r ** 2))
                T[ix_min:ix_max, iy_min:iy_max, iz_min:iz_max] += sub_dt * q_sub / rho_cp

            current_time += dt

            # 采集动画帧
            if self.save_animation and idx % anim_step == 0 and len(self.animation_frames) < 100:
                self.animation_frames.append(T[:, :, nz // 2].copy())
                self.animation_frame_times.append(current_time)

            # 更新进度
            if idx % progress_step == 0:
                progress = (idx + 1) / total_steps * 100
                # print(progress, f"计算温度场... {progress:.0f}% ({idx + 1}/{total_steps})")
                self.progress_update.emit(progress, f"计算温度场... {progress:.0f}%")

        # 保存最后一帧
        if self.save_animation and len(self.animation_frames) < 100:
            self.animation_frames.append(T[:, :, nz // 2].copy())
            self.animation_frame_times.append(current_time)

        self.status_update.emit("温度场计算完成！", "success")

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

        # 4. 绑定UI控件事件
        self._bind_ui_events()

        # 5. 初始化默认配置
        self.set_default_values()  # 设置默认参数
        self.init_status_frame()  # 初始化状态显示区
        self.disable_animation_buttons()  # 初始禁用动画按钮
        # 定义刀具和激光轨迹x，y画布范围
        Lx, Ly, Lz = 0.1, 0.1, 0.005
        self.x_scope = [-0.02, Lx]
        self.y_scope = [-0.02, Ly]
        # 定义激光轨迹点
        self.x_laser = []
        self.y_laser = []
        self.vLaser = 0
        self.nt_fit_cutter=0 # 这是原始轨迹能够配合刀具轨迹运动的总点数

        # 存储各图最新数据（用于页面切换后刷新）
        self.cutter_data = None  # 刀具轨迹数据
        self.laser_data = None  # 激光轨迹数据
        self.heat_data = None  # 热场数据（含动画帧）
        self.heat_animation_controller = None  # 动画控制器

        self.switch_to_page(0)  # 默认显示刀具轨迹页

    # ========================== UI事件绑定 ==========================
    def _bind_ui_events(self):
        """绑定所有UI控件和相应事件处理函数"""
        # 轨迹生成按钮
        self.btn_cutter.clicked.connect(self.cutter_traj_gen)
        self.btn_laser.clicked.connect(self.laser_traj_gen)

        # 温度场计算按钮
        self.btn_heat_even.clicked.connect(self.heat_traj_gen_even)
        # 激光轨迹智能优化按钮
        self.btn_opt_laser.clicked.connect(self.laser_traj_optimize)

        # 坐标输入按钮
        self.btn_open_coords.clicked.connect(self.open_coord_dialog)

        # 轨迹类型选择框
        self.comboBox_trajectory_type.setCurrentIndex(0)
        self.stackedWidget_params.setCurrentIndex(0)
        self.comboBox_trajectory_type.currentIndexChanged.connect(self.get_trajectory_parameters)

        # 页面切换按钮
        self.btn_cutter_change.clicked.connect(lambda: self.switch_to_page(0))
        self.btn_laser_change.clicked.connect(lambda: self.switch_to_page(1))
        self.btn_heat_change.clicked.connect(lambda: self.switch_to_page(2))

        # 动画控制按钮（后续动态绑定）
        self.connect_animation_buttons()

    # ========================== 页面切换逻辑 ==========================
    def switch_to_page(self, index):
        """0:刀具轨迹, 1:激光轨迹, 2:热场"""
        old_index = self.stackedWidget.currentIndex()
        self.stackedWidget.setCurrentIndex(index)

        # 离开热场页面时暂停动画
        if old_index == 2 and self.heat_animation_controller:
            if self.heat_animation_controller.is_playing:
                self.heat_animation_controller.pause()
                self.update_animation_button_states(is_playing=False)

        # 刷新当前页面显示
        if index == 0:
            self._refresh_cutter_display()
        elif index == 1:
            self._refresh_laser_display()
        elif index == 2:
            self._refresh_heat_display()

    def _refresh_cutter_display(self):
        if self.cutter_data is None:
            self.show_status_message("尚未生成刀具轨迹", "warning")
            return
        fig = cutter_matplotlib_plot(
            self.cutter_data['x'], self.cutter_data['y'],
            self.cutter_data['ret'], self.cutter_data['x_scope'], self.cutter_data['y_scope']
        )
        display_plot_on_label(fig, self.cutter_plot_display)

    def _refresh_laser_display(self):
        if self.laser_data is None:
            self.show_status_message("尚未生成激光轨迹", "warning")
            return
        fig = laser_matplotlib_plot(
            self.laser_data['x_cutter'], self.laser_data['y_cutter'],
            self.laser_data['ret'], self.laser_data['rb0'],
            self.laser_data['x_laser'], self.laser_data['y_laser'],
            self.laser_data['x_scope'], self.laser_data['y_scope'],
            self.laser_data['is_opt']
        )
        self.laser_plot_widget.set_figure(fig)

        # ==================== 热场显示与动画核心修改（简化版） ====================

    def _refresh_heat_display(self):
        """刷新热场页面显示（静态图 + 动画） - 安全替换版"""
        if self.heat_data is None:
            self.show_status_message("尚未生成热场图", "warning")
            return

        # 1. 显示静态温度场图（与原逻辑相同）
        try:
            fig = heat_even_matplotlib_plot(
                self.heat_data['x'], self.heat_data['y'],
                self.heat_data['nz'], self.heat_data['T'],
                self.heat_data['traj_type']
            )
            display_plot_on_label(fig, self.heat_plot_display)
        except Exception as e:
            self.show_status_message(f"静态温度场图绘制失败: {e}", "error")
            traceback.print_exc()

        # 2. 处理动画部分：安全替换
        container = self.heat_animation_container

        # 停止并销毁旧动画控制器
        if self.heat_animation_controller is not None:
            self.heat_animation_controller.close()
            self.heat_animation_controller = None

        # 清空容器中的所有子控件（保留布局结构）
        layout = container.layout()
        if layout is None:
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        else:
            # 移除所有子控件，但不删除布局
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # 3. 如果有动画数据，创建新的动画控制器
        if (self.heat_data.get('animation_frames') and
                self.heat_data.get('animation_frame_times') and
                len(self.heat_data['animation_frames']) > 0):
            try:
                # 创建控制器，它会将自己的画布添加到布局中
                self.heat_animation_controller = HeatAnimationController(
                    container, layout,  # 传入容器和布局
                    self.heat_data['x'], self.heat_data['y'],
                    self.heat_data['animation_frames'],
                    self.heat_data['animation_frame_times'],
                    self.heat_data['traj_type']
                )
                if self.heat_animation_controller and self.heat_animation_controller.canvas:
                    self.connect_animation_buttons()
                    self.enable_animation_buttons()
                    self.update_animation_button_states(is_playing=False)
                    self.show_status_message("动画加载成功", "success")
                else:
                    self.disable_animation_buttons()
                    self.show_status_message("动画创建失败", "error")
            except Exception as e:
                self.disable_animation_buttons()
                self.show_status_message(f"创建动画时发生异常: {e}", "error")
                traceback.print_exc()
        else:
            self.disable_animation_buttons()
            self.show_status_message("无动画数据", "warning")

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
        timestamp = datetime.now().strftime("%H:%M:%S")
        style_config = {
            "info": {"color": "#333333", "prefix": "[INFO]"},
            "warning": {"color": "#ff9900", "prefix": "[WARN]"},
            "error": {"color": "#ff0000", "prefix": "[ERROR]"},
            "success": {"color": "#009900", "prefix": "[SUCCESS]"}
        }
        config = style_config.get(message_type, style_config["info"])
        safe_message = html.escape(message)

        # 使用 div 控制行间距和字体，去除额外边距
        html_msg = f'<div style="margin:0; padding:0; line-height:1.2; font-size:9pt;">'
        html_msg += f'<span style="color:{config["color"]};">[{timestamp}] <b>{config["prefix"]}</b> {safe_message}</span>'
        html_msg += f'</div>'

        self.textEdit_status.append(html_msg)

        if hasattr(self, 'checkBox_auto_scroll') and self.checkBox_auto_scroll.isChecked():
            scrollbar = self.textEdit_status.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

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
                "lineEdit_Det": "15e-3",  # 刀具直径 (m)
                "lineEdit_ae": "12e-3",  # 切削宽度 (m)
                "lineEdit_ap": "-0.26e-3",  # 切削深度 (m)
                "lineEdit_nC": "400",  # 主轴转速 (r/min) # 这两个参数其实应该可以合并
                "lineEdit_fz": "0.5e-3",  # 每齿进给量 (m)
                "lineEdit_k": "15",  # 热传导系数 (W/(m·K))
                "lineEdit_rho": "7800",  # 材料密度 (kg/m³)
                "lineEdit_cp": "500",  # 比热容 (J/(kg·K))
                "lineEdit_source_power": "2000",  # 激光功率 (W)
                "lineEdit_rb0": "1.5e-3",  # 激光光斑半径 (m)
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
        """提取所有输入参数（材料、激光、切削参数），也是在计算轨迹和温度场时调用"""
        try:
            # 从UI控件读取参数
            ret = float(self.lineEdit_Det.text()) / 2  # 刀具有效半径 (m)
            ae = float(self.lineEdit_ae.text())  # 切削宽度 (m)
            ap = float(self.lineEdit_ap.text())  # 切削深度 (m)
            nr = eval(self.lineEdit_nC.text())  # 主轴转速 (r/min)
            # fz = float(self.lineEdit_fz.text())  # 每齿进给量 (m)
            k = float(self.lineEdit_k.text())  # 热传导系数 (W/(m·K))
            rho = float(self.lineEdit_rho.text())  # 材料密度 (kg/m³)
            cp = float(self.lineEdit_cp.text())  # 比热容 (J/(kg·K))
            laser_p = float(self.lineEdit_source_power.text())  # 激光功率 (W)
            laser_r = eval(self.lineEdit_rb0.text())  # 激光光斑半径 (m)


            # 返回参数字典
            return {
                'ret': ret, 'ae': ae, 'ap': ap, 'nr': nr,
                'k': k, 'rho': rho, 'cp': cp, 'laser_p': laser_p,
                'laser_r': laser_r,
                'coordinates': self.coordinates if self.coordinates else [(0.0, 0.0)]
            }
        except ValueError as e:
            raise ValueError(f"参数转换错误: {e}")
        except Exception as e:
            raise Exception(f"获取参数时出错: {e}")

    def _get_con_array(self, params):

        """设置默认参数与计算得到的参数，构建轨迹生成函数所需的配置数组"""
        # 一些默认参数：
        fz = 0.5e-03  # 每齿进给量
        tooth_number = 4  # 铣刀齿数

        dt=0.00048  # 原始激光轨迹仿真时间步长

        # 计算派生参数
        # wC = nC * 2 * np.pi/60  # 主轴角速度 (rad/s)
        scan_angle = 2 * np.arcsin(params['ae'] / 2 / params['ret'])  # 激光扫描角 (rad)
        fr = fz * tooth_number  # 每转进给距离 (m/r)
        fx = fr * params['nr'] / 60  # X方向进给率 (m/s)，认为为进给率
        fy = 0

        # 获取坐标起点
        if self.coordinates:
            X0Cutter = self.coordinates[0][0]
            Y0Cutter = self.coordinates[0][1]
        else:
            X0Cutter = 0.0
            Y0Cutter = 0.0
            self.show_status_message("警告：坐标列表为空，使用默认起点 (0,0)", "warning")

        # 激光起点X坐标（相对于刀具偏移5.5mm），这个偏移量也是可以修改的
        bias = 5.5e-3
        X0Laser = X0Cutter + bias # 可是一开始不是在Y方向上偏置吗，我觉得有问题

        # 配置数组（各元素含义见轨迹生成函数文档）
        return {
            "ae": params['ae'], "ap": params['ap'],  # 铣削参数：铣削宽度，铣削深度，刀具有效半径
            "ret": params['ret'], "fz":fz,"tooth_number":tooth_number,"nr":params["nr"],  # 刀具参数：刀具有效直径、每齿进给量、齿数、主轴转速
            "alpha":params['k'] / (params['cp'] * params['rho']),  # 材料参数：热扩散系数 alpha
            "laser_r": params['laser_r'], "scan_angle":scan_angle, "beta_b":50,  # 激光参数：激光半径，激光扫描角度，beta_b = 50
            "X0Cutter":X0Cutter, "Y0Cutter":Y0Cutter,  # 刀具起点坐标
            "X0Laser":X0Laser,
            # "Y0Laser":params['Y0Laser'],
            "bias":5.5e-3, # 激光起点X、Y坐标，激光起点相对于刀具起点偏置
            "base_factor":1, "sharpness_factor":0.5, #base_factor, sharpness_factor（这个是角度因子修正曲率）
            'coordinates':params['coordinates'], # 刀具所有经过的轨迹点coordinates
            "fx":fx, "fy":fy,   # 刀具运动参数：x方向刀具进给速度，认为为进给率, fy# 这里设定 fy=0
            "parallNr":2, "dt":dt,  # 仿真参数：parallNr,时间步长
            "memAvailableGB(仿真参数）": 12, "nodesNrX": 50, "nodesNrY": 40, "nodesNrZ": 1,  # intPointNr, nodesNrX/Y/Z,
            "intPointNr": 4000, "pointOfOnePass": 100,  # pointOfOnePass(一段刀具轨迹对应激光扫描的点数）, 这个一定要改
        }

    # ========================== 坐标管理 ==========================
    def open_coord_dialog(self): #后续G代码里面的坐标就要输进去
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
                # self.show_status_message(f"从对话框获取到 {len(new_coords)} 个坐标", "info")

                if new_coords:
                    # 更新坐标存储,此时类变量coordinates已经有了值
                    self.coordinates = new_coords
                    self.saved_coordinates = new_coords.copy()
                    self.last_coordinates = new_coords.copy()

                    # 显示坐标点信息
                    # for i, (x, y) in enumerate(new_coords):
                    #     self.show_status_message(f"点{i + 1}: ({x:.6f}, {y:.6f})", "info")
                else:
                    self.show_status_message("没有输入有效坐标", "info")

        except Exception as e:
            self.show_status_message(f"打开坐标对话框时出错: {e}", "error")
            traceback.print_exc()

# 真正执行计算部分
    # ========================== 轨迹生成 ==========================
    def cutter_traj_gen(self):
        try:
            common_params = self._get_common_parameters()
            traj_params = self.get_current_trajectory_params()
            con_array = self._get_con_array(common_params)

            # self.show_status_message(f"生成多段轨迹，共{len(self.coordinates)}个点", "info")
            x_cutter, y_cutter, cutter_info = cutter_trajectory(con_array, common_params['coordinates'])

            # 存储数据
            self.cutter_data = {
                'x': x_cutter, 'y': y_cutter,
                'ret': common_params['ret'],
                'x_scope': self.x_scope, 'y_scope': self.y_scope
            }

            self.show_status_message("生成刀具轨迹完毕", "success")
            # 如果当前页面是刀具轨迹页则刷新，否则提示
            if self.stackedWidget.currentIndex() == 0:
                self._refresh_cutter_display()
            else:
                self.show_status_message("刀具轨迹已生成，切换至【刀具轨迹页面】查看", "info")

        except Exception as e:
            self.show_status_message(f"计算错误: {e}", "error")

    def laser_traj_gen(self):
        try:
            common_params = self._get_common_parameters()
            traj_params = self.get_current_trajectory_params()
            con_array = self._get_con_array(common_params)

            x_cutter, y_cutter, cutter_info = cutter_trajectory(con_array, common_params['coordinates'])
            x_rotated, y_rotated, vLaser = sweeping_laser_trajectory_with_distance_preservation(
                con_array, traj_params, x_cutter, y_cutter, cutter_info
            )

            self.x_laser = np.concatenate(x_rotated)
            self.y_laser = np.concatenate(y_rotated)
            self.vLaser=vLaser
            self.nt_fit_cutter = len(self.x_laser)

            # 存储数据
            self.laser_data = {
                'x_cutter': x_cutter, 'y_cutter': y_cutter,
                'ret': common_params['ret'], 'rb0': common_params['laser_r'],
                'x_laser': x_rotated, 'y_laser': y_rotated,
                'x_scope': self.x_scope, 'y_scope': self.y_scope,
                'is_opt': False
            }

            self.show_status_message("生成激光轨迹完毕", "success")
            if self.stackedWidget.currentIndex() == 1:
                self._refresh_laser_display()
            else:
                self.show_status_message("激光轨迹已生成，切换至【激光扫描轨迹页面】查看", "info")


        except Exception as e:
            self.show_status_message(f"计算错误: {e}", "error")

    def laser_traj_optimize(self):
        try:
            common_params = self._get_common_parameters()
            traj_params = self.get_current_trajectory_params()
            con_array = self._get_con_array(common_params)

            self.show_status_message("激光轨迹正在优化中，请稍后", "info")

            x_cutter, y_cutter, cutter_info = cutter_trajectory(con_array, common_params['coordinates'])
            x_rotated, y_rotated, vLaser = sweeping_laser_trajectory_optimized(
                con_array, traj_params, x_cutter, y_cutter, cutter_info
            )
            self.x_laser = np.concatenate(x_rotated)
            self.y_laser = np.concatenate(y_rotated)
            self.vLaser=vLaser

            # 存储数据
            self.laser_data = {
                'x_cutter': x_cutter, 'y_cutter': y_cutter,
                'ret': common_params['ret'], 'rb0': common_params['laser_r'],
                'x_laser': x_rotated, 'y_laser': y_rotated,
                'x_scope': self.x_scope, 'y_scope': self.y_scope,
                'is_opt': True
            }

            time_length=2*round(len(self.x_laser)/4600)
            time.sleep(time_length)
            self.show_status_message("优化激光轨迹完毕", "success")

            # 下面代码意思是，当你已经在激光扫描轨迹页面，就不会再显示“"激光轨迹已优化，切换至【激光扫描轨迹页面】查看"”，如果不在，会显示这个
            if self.stackedWidget.currentIndex() == 1:
                self._refresh_laser_display()
            else:
                self.show_status_message("激光轨迹已优化，切换至【激光扫描轨迹页面】查看", "info")

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
            self.heat_thread = HeatTrajThread(con_array, common_params, traj_params, is_even, x_laser=self.x_laser, y_laser=self.y_laser,
                                              vLaser=self.vLaser, nt_fit_cutter=self.nt_fit_cutter)
            self._setup_heat_thread_connections()
            self.heat_thread.start()

            # 3. 禁用计算按钮避免重复点击
            self.btn_heat_even.setEnabled(False)
            # 加代码防抖
            QTimer.singleShot(500, lambda: self.btn_opt_laser.setEnabled(True))

        except Exception as e:
            self.show_status_message(f"启动热轨迹计算失败: {e}", "error")

# 真正执行计算部分
#     def heat_traj_gen(self):
#         """启动普通算法的温度场计算（多线程）"""
#         self._start_heat_calculation(is_even=False)

    def heat_traj_gen_even(self):
        """使用正常算法计算热场"""
        self._start_heat_calculation(is_even=False)


    @pyqtSlot(float, str)
    def _update_progress(self, progress, message):
        """更新计算进度显示"""
        self.show_status_message(message, "info")
        # 如需进度条，可在此添加：self.progressBar.setValue(int(progress))

    @pyqtSlot(object)
    def _on_heat_calculation_finished(self, result):
        try:
            # 存储热场数据
            self.heat_data = {
                'x': result['x'], 'y': result['y'], 'nz': result['nz'],
                'T': result['T'], 'traj_type': result['traj_type'],
                'animation_frames': result.get('animation_frames'),
                'animation_frame_times': result.get('animation_frame_times')
            }

            if self.stackedWidget.currentIndex() == 2:
                self._refresh_heat_display()
            else:
                self.show_status_message("热场图已生成，切换至【热场动画页面】查看", "info")

            # method_name = "等弧长采样" if result['method'] == 'even' else ""
            # self.show_status_message(f"生成{method_name}温度场二维切片图完毕", "success")
            # self.show_status_message(f"生成温度场二维切片图完毕", "success")
        except Exception as e:
            self.show_status_message(f"图形创建失败: {e}", "error")
            traceback.print_exc()
            self.disable_animation_buttons()
        finally:
            self.btn_heat_even.setEnabled(True)
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