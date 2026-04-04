"""
激光辅助加工路径可视化模块
核心功能：
1. 静态绘图：刀具轨迹、激光轨迹、温度场分布
2. 动态绘图：温度场动画播放/暂停/重置/保存
3. 辅助功能：Matplotlib图形转Qt控件显示
"""

# ============================== 导入模块区（按功能分组）==============================
# 1. 标准库模块
import traceback
from io import BytesIO

# 2. 第三方数值计算/可视化模块
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
# 3. PyQt5 GUI相关模块
from PyQt5.QtCore import QTimer,QObject
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QSizePolicy,
)

# 新增：Matplotlib+Qt交互依赖
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QWidget, QVBoxLayout
# ============================== 全局配置 ==============================
# 设置Matplotlib中文字体（避免中文乱码）
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置默认中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块的问题


# ============================== 核心工具函数 ==============================
def display_plot_on_label(fig, label_widget):
    """
    将Matplotlib生成的图形显示到Qt的QLabel控件中
    参数：
        fig: Matplotlib的Figure对象（绘图结果）
        label_widget: QLabel控件对象（用于显示图形）
    实现逻辑：
        1. 将Figure对象保存为PNG格式的字节流
        2. 将字节流转换为QPixmap
        3. 在QLabel中显示Pixmap并开启自动缩放
    """
    try:
        # 步骤1：创建字节流缓冲区，将图形保存为PNG格式
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format='png',
            dpi=100,  # 分辨率
            bbox_inches='tight'  # 紧凑布局，去除多余空白
        )
        buffer.seek(0)  # 将文件指针移到开头

        # 步骤2：将字节流转换为QPixmap并显示
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())  # 从字节流加载图片
        label_widget.setPixmap(pixmap)  # 设置QLabel显示的图片
        label_widget.setScaledContents(True)  # 开启自动缩放，适应QLabel大小

    except Exception as e:
        print(f"图形显示到QLabel失败: {e}")
        traceback.print_exc()
    finally:
        # 步骤3：清理资源，避免内存泄漏
        plt.close(fig)  # 关闭Matplotlib图形
        buffer.close()  # 关闭字节流


# ============================== 静态绘图函数（轨迹/温度场）=============================
def cutter_matplotlib_plot(x, y, ret, x_scope, y_scope):
    """
    绘制刀具轨迹静态图
    参数：
        x: 刀具轨迹X坐标数组 (m)
        y: 刀具轨迹Y坐标数组 (m)
        Ret: 刀具半径 (m)
        cutter_traj_type: 轨迹类型字符串（如"line"/"sin"/"zigzag"）
    返回：
        fig: Matplotlib的Figure对象（包含绘制好的轨迹图）
    绘制逻辑：
        1. 创建画布和坐标轴
        2. 绘制轨迹线
        3. 计算坐标轴范围（添加边距保证刀具完整显示）
        4. 绘制刀具起点/终点（圆形）
        5. 设置图形样式（标题、标签、图例、网格）
        6. 调整布局并返回Figure对象
    """
    # 步骤1：创建绘图画布（8x6英寸，适合Qt控件显示）
    fig, ax = plt.subplots(figsize=(8, 6))

    # 步骤2：绘制刀具轨迹线（蓝色实线，2px宽度）
    ax.plot(x, y, 'b-', linewidth=2, label="刀具轨迹")

    # ========== 核心修改：替换原有自动计算范围的逻辑 ==========
    # 直接使用指定的x_scope/y_scope作为坐标轴范围，不再自动计算
    ax.set_xlim(x_scope[0], x_scope[1])  # X轴范围：用户指定的上下限
    ax.set_ylim(y_scope[0], y_scope[1])  # Y轴范围：用户指定的上下限

    # # 步骤3：计算坐标轴显示范围（添加刀具半径1.5倍的边距，保证刀具完整显示）
    # x_min, x_max = np.min(x), np.max(x)
    # y_min, y_max = np.min(y), np.max(y)
    # margin = Ret * 1.5  # 边距 = 刀具半径 × 1.5
    # ax.set_xlim(x_min - margin, x_max + margin)
    # ax.set_ylim(y_min - margin, y_max + margin)

    # 步骤4：绘制刀具起点和终点（圆形，使用matplotlib.patches.Circle保证形状准确）
    # 起点：紫红色半透明圆 + 黑色X标记
    start_circle = Circle(
        (x[0], y[0]), ret,  # 圆心坐标 + 半径
        color='#D6009B', alpha=0.6,  # 颜色（紫红色）+ 透明度
        label='刀具起点'  # 图例标签
    )
    ax.add_patch(start_circle)

    # 终点：青绿色半透明圆 + 黑色X标记
    end_circle = Circle(
        (x[-1], y[-1]), ret,  # 圆心坐标 + 半径
        color='#00C1B3', alpha=0.6,  # 颜色（青绿色）+ 透明度
        label='刀具终点'  # 图例标签
    )
    ax.add_patch(end_circle)

    # 步骤5：在起点/终点中心添加X标记（增强视觉效果）
    ax.scatter(
        [x[0], x[-1]], [y[0], y[-1]],  # 标记坐标
        color=['black', 'black'],  # 标记颜色
        s=20, marker='x', zorder=10  # 大小 + 形状 + 层级（置顶显示）
    )

    # 步骤6：设置图形样式和标签
    ax.set_xlabel('X/m')  # X轴标签
    ax.set_ylabel('Y/m')  # Y轴标签
    ax.set_title(f'刀具轨迹')  # 图形标题
    ax.set_aspect('equal')  # 等比例坐标轴（保证圆形显示为正圆）
    ax.grid(True)  # 显示网格线

    # 步骤7：创建去重后的图例（避免重复标签）
    unique_labels = []
    unique_handles = []
    # 手动构建图例句柄（轨迹线 + 起点圆 + 终点圆）
    legend_items = [
        (Line2D([0], [0], color='b', linewidth=2, label="刀具轨迹"), "刀具轨迹"),
        (start_circle, '刀具起点'),
        (end_circle, '刀具终点')
    ]
    # 去重逻辑：只保留首次出现的标签
    for handle, label in legend_items:
        if label not in unique_labels:
            unique_labels.append(label)
            unique_handles.append(handle)
    ax.legend(unique_handles, unique_labels)

    # 步骤8：调整布局（自动适配，避免标签重叠）
    plt.tight_layout()

    return fig


def laser_matplotlib_plot(x_cutter, y_cutter, Ret, rb0, x_laser=None, y_laser=None,
                          x_scope=None, y_scope=None, is_opt=False):
    """
    绘制刀具+激光轨迹对比静态图
    支持两种输入格式：
    1. 一维数组：x_laser, y_laser 为整个轨迹的坐标（原有方式）
    2. 二维分段结构：x_laser, y_laser 为列表，每个元素是一段轨迹的坐标数组
       此时会分段绘制，段间用红色虚线连接
    """
    Ret = float(Ret)
    rb0 = float(rb0)
    x_cutter = np.array(x_cutter, dtype=float)
    y_cutter = np.array(y_cutter, dtype=float)

    fig, ax = plt.subplots(constrained_layout=True)

    # 绘制刀具轨迹
    line_cutter = ax.plot(x_cutter, y_cutter, 'b-', linewidth=2, label="刀具轨迹")[0]
    cutter_start_circle = Circle((x_cutter[0], y_cutter[0]), Ret, color='#D6009B', alpha=0.6, label='刀具起点')
    cutter_end_circle = Circle((x_cutter[-1], y_cutter[-1]), Ret, color='#00C1B3', alpha=0.6, label='刀具终点')
    ax.add_patch(cutter_start_circle)
    ax.add_patch(cutter_end_circle)
    ax.scatter([x_cutter[0], x_cutter[-1]], [y_cutter[0], y_cutter[-1]], color='black', s=20, marker='x', zorder=10)

    # 判断是否为分段数据
    is_segmented = False
    if x_laser is not None and y_laser is not None:
        # 检查是否为列表/元组，且第一个元素是数组或列表
        if isinstance(x_laser, (list, tuple)) and len(x_laser) > 0:
            first = x_laser[0]
            if isinstance(first, (list, np.ndarray)):
                is_segmented = True

    laser_plotted = False
    line_laser = None
    laser_start_circle = None
    laser_end_circle = None
    connection_lines = []  # 存储连接线的句柄，用于图例

    if x_laser is not None and y_laser is not None:
        laser_plotted = True

        if is_segmented:
            # ========== 分段绘制模式 ==========
            num_segments = len(x_laser)
            # 用于图例去重
            laser_label_added = False
            conn_label_added = False

            for i in range(num_segments):
                x_seg = np.array(x_laser[i], dtype=float)
                y_seg = np.array(y_laser[i], dtype=float)
                if len(x_seg) == 0:
                    continue

                # 绘制当前段（黄色实线）
                label = "激光轨迹" if not laser_label_added else ""
                line = ax.plot(x_seg, y_seg, color='y', linewidth=1.5, alpha=0.7, label=label)[0]
                if not laser_label_added:
                    line_laser = line
                    laser_label_added = True

                # 如果不是最后一段，绘制到下一段的连接线（红色虚线）
                if i < num_segments - 1:
                    # 本段终点
                    x_end = x_seg[-1]
                    y_end = y_seg[-1]
                    # 下一段起点
                    x_next_start = np.array(x_laser[i+1], dtype=float)[0]
                    y_next_start = np.array(y_laser[i+1], dtype=float)[0]
                    conn_label = "段间连接" if not conn_label_added else ""
                    conn_line = ax.plot([x_end, x_next_start], [y_end, y_next_start],
                                        'r--', linewidth=1.2, alpha=0.8, label=conn_label)[0]
                    if not conn_label_added:
                        connection_lines.append(conn_line)
                        conn_label_added = True

            # 激光起点（第一段第一个点）和终点（最后一段最后一个点）
            first_x = np.array(x_laser[0], dtype=float)[0]
            first_y = np.array(y_laser[0], dtype=float)[0]
            last_x = np.array(x_laser[-1], dtype=float)[-1]
            last_y = np.array(y_laser[-1], dtype=float)[-1]

            laser_start_circle = Circle((first_x, first_y), rb0, color='#FF6B35', alpha=0.6, label='激光起点')
            laser_end_circle = Circle((last_x, last_y), rb0, color='#7A4FFF', alpha=0.6, label='激光终点')
            ax.add_patch(laser_start_circle)
            ax.add_patch(laser_end_circle)
            ax.scatter([first_x, last_x], [first_y, last_y], color='black', s=10, marker='+', zorder=10)

        else:
            # ========== 原有的一维数组模式 ==========
            x_laser = np.array(x_laser, dtype=float)
            y_laser = np.array(y_laser, dtype=float)
            line_laser = ax.plot(x_laser, y_laser, color='y', linewidth=1.5, alpha=0.7, label="激光轨迹")[0]
            laser_start_x, laser_start_y = x_laser[0], y_laser[0]
            laser_end_x, laser_end_y = x_laser[-1], y_laser[-1]
            laser_start_circle = Circle((laser_start_x, laser_start_y), rb0, color='#FF6B35', alpha=0.6, label='激光起点')
            laser_end_circle = Circle((laser_end_x, laser_end_y), rb0, color='#7A4FFF', alpha=0.6, label='激光终点')
            ax.add_patch(laser_start_circle)
            ax.add_patch(laser_end_circle)
            ax.scatter([laser_start_x, laser_end_x], [laser_start_y, laser_end_y], color='black', s=10, marker='+', zorder=10)

    # 坐标轴范围
    ax.margins(0, 0)
    ax.set_xlim(x_scope[0], x_scope[1])
    ax.set_ylim(y_scope[0], y_scope[1])

    ax.set_xlabel('X/m', fontsize=10)
    ax.set_ylabel('Y/m', fontsize=10)
    plt.axis('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.ticklabel_format(style='sci', axis='both', scilimits=(0, 0))
    ax.set_title('优化刀具与激光轨迹' if is_opt else '原始刀具与激光轨迹', fontsize=10, fontweight='bold')

    # 构建图例（去重）
    handles = [line_cutter, cutter_start_circle, cutter_end_circle]
    labels = ["刀具轨迹", "刀具起点", "刀具终点"]
    if laser_plotted:
        if line_laser is not None:
            handles.append(line_laser)
            labels.append("激光轨迹")
        if laser_start_circle is not None:
            handles.append(laser_start_circle)
            labels.append("激光起点")
        if laser_end_circle is not None:
            handles.append(laser_end_circle)
            labels.append("激光终点")
        # 添加连接线图例（如果有）
        if connection_lines:
            # 只取第一条连接线代表
            handles.append(connection_lines[0])
            labels.append("段间连接")

    ax.legend(handles=handles, labels=labels, loc='center left',
              bbox_to_anchor=(1.01, 0.5), fontsize=10, frameon=True)

    return fig


def heat_even_matplotlib_plot(x, y, nz, T, cutter_traj_type):
    fig, ax = plt.subplots(figsize=(8, 6))
    T_middle = T[:, :, nz // 2].T  # 形状 (ny, nx)

    # 使用 imshow 替代 contourf，并设置平滑插值
    extent = [x.min(), x.max(), y.min(), y.max()]
    im = ax.imshow(T_middle,
                   extent=extent,
                   origin='lower',
                   cmap='hot',
                   interpolation='bilinear',  # 关键：双线性插值
                   aspect='auto')

    plt.colorbar(im, label='温度 (K)')
    ax.set_title(f'{cutter_traj_type}轨迹相配合激光均匀温度场分布')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    plt.tight_layout()
    return fig


# ============================== 动态动画类（温度场）=============================
class HeatAnimationController(QObject):
    """温度场动画控制器 - 极简版，只负责画布和定时器"""

    def __init__(self, container, layout, x, y, frames, times, traj_type):
        super().__init__()
        self.container = container
        self.layout = layout
        self.frames = frames
        self.times = times
        self.current_frame = 0
        self.is_playing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)

        # 创建 matplotlib 图形
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=80)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 将画布添加到布局
        self.layout.addWidget(self.canvas)

        # 计算温度范围
        all_temps = np.concatenate([f.flatten() for f in frames])
        valid = all_temps[~np.isnan(all_temps)]
        if len(valid) > 0:
            self.vmin, self.vmax = valid.min(), valid.max()
            if self.vmin == self.vmax:
                self.vmin -= 0.1
                self.vmax += 0.1
        else:
            self.vmin, self.vmax = 0, 1

        # 坐标范围
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        if x_min == x_max:
            x_min, x_max = x_min - 0.1, x_max + 0.1
        if y_min == y_max:
            y_min, y_max = y_min - 0.1, y_max + 0.1
        self.extent = [x_min, x_max, y_min, y_max]

        # 第一帧
        first = frames[0]
        if first.ndim == 1:
            first = first.reshape(-1, 1)
        self.im = self.ax.imshow(first.T, extent=self.extent, origin='lower',
                                 cmap='hot', vmin=self.vmin, vmax=self.vmax,
                                 aspect='auto', interpolation='bilinear')
        self.fig.colorbar(self.im, ax=self.ax, label='温度 (K)')
        self.ax.set_xlabel('X/m')
        self.ax.set_ylabel('Y/m')
        self.ax.set_title(f'温度场分布 (时间: {times[0]:.4f} s)')

        self.canvas.draw()

    def _update_frame(self):
        if not self.is_playing:
            return
        if self.current_frame >= len(self.frames):
            self.current_frame = 0
        frame = self.frames[self.current_frame]
        if frame.ndim == 1:
            frame = frame.reshape(-1, 1)
        self.im.set_data(frame.T)
        self.ax.set_title(f'温度场分布 (时间: {self.times[self.current_frame]:.4f} s)')
        self.canvas.draw_idle()
        self.current_frame += 1

    def play(self):
        if not self.is_playing:
            if self.current_frame >= len(self.frames):
                self.current_frame = 0
            self.timer.start(200)
            self.is_playing = True

    def pause(self):
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False

    def reset(self):
        self.pause()
        self.current_frame = 0
        frame = self.frames[0]
        if frame.ndim == 1:
            frame = frame.reshape(-1, 1)
        self.im.set_data(frame.T)
        self.ax.set_title(f'温度场分布 (时间: {self.times[0]:.4f} s)')
        self.canvas.draw_idle()

    def save(self, parent=None):
        # 简化保存逻辑，与原类似
        if not self.frames:
            return False
        path, _ = QFileDialog.getSaveFileName(parent, "保存动画", "", "GIF (*.gif);;MP4 (*.mp4)")
        if not path:
            return False
        if not path.endswith(('.gif', '.mp4')):
            path += '.gif'
        try:
            from matplotlib.animation import FuncAnimation
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(self.frames[0].T, extent=self.extent, origin='lower',
                           cmap='hot', vmin=self.vmin, vmax=self.vmax, aspect='auto')
            fig.colorbar(im, label='温度 (K)')
            ax.set_xlabel('X/m')
            ax.set_ylabel('Y/m')

            def update(i):
                im.set_data(self.frames[i].T)
                ax.set_title(f'温度场分布 (时间: {self.times[i]:.4f} s)')
                return im,

            ani = FuncAnimation(fig, update, frames=len(self.frames), interval=200, blit=True)
            if path.endswith('.gif'):
                ani.save(path, writer='pillow', fps=5)
            else:
                ani.save(path, writer='ffmpeg', fps=5)
            plt.close(fig)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def close(self):
        self.pause()
        self.timer = None
        if self.canvas:
            self.layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
            self.canvas = None
        if self.fig:
            plt.close(self.fig)
            self.fig = None

# ============================== 动画创建工具函数 ==============================
# def create_simple_heat_animation(container, x, y, animation_frames, animation_frame_times, traj_type):
#     try:
#         return HeatAnimationController(container, x, y, animation_frames, animation_frame_times, traj_type)
#     except Exception as e:
#         print(f"创建温度场动画失败: {e}")
#         traceback.print_exc()
#         return None


# 交互式绘图控件类
class InteractiveMatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setStretch(0, 1)

        self.canvas = None
        self.toolbar = None

    def set_figure(self, fig):
        if self.canvas is not None:
            self._layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
        if self.toolbar is not None:
            self._layout.removeWidget(self.toolbar)
            self.toolbar.deleteLater()

        fig.patch.set_facecolor('white')

        # fig.subplots_adjust(left=0.05, right=0.85, top=0.95, bottom=0.05)

        self.canvas = FigureCanvas(fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()

        self.toolbar = NavigationToolbar(self.canvas, self)
        self._layout.addWidget(self.toolbar)
        self._layout.addWidget(self.canvas)


        self.canvas.draw()
        self.update()

# def heat_matplotlib_plot(x, y, nz, T, cutter_traj_type):
#     """
#     绘制普通算法温度场二维切片图（z方向中间层）
#     参数：
#         x: X轴坐标数组 (m)
#         y: Y轴坐标数组 (m)
#         nz: Z方向网格数量
#         T: 温度场三维数组 (nx × ny × nz)，单位K
#         cutter_traj_type: 轨迹类型字符串（如"line"/"sin"/"zigzag"）
#     返回：
#         fig: Matplotlib的Figure对象（包含温度场分布图）
#     绘制逻辑：
#         1. 创建画布和坐标轴
#         2. 提取z方向中间层温度数据
#         3. 绘制等高线填充图（hot色图，体现温度分布）
#         4. 添加颜色条（标注温度单位）
#         5. 设置标题和坐标轴标签
#         6. 调整布局并返回Figure对象
#     """
#     # 步骤1：创建绘图画布（8x6英寸）
#     fig, ax = plt.subplots(figsize=(8, 6))
#
#     # 步骤2：提取z方向中间层温度数据
#     middle_slice = nz // 2  # 中间层索引
#     T_middle = T[:, :, middle_slice]  # 中间层温度数据
#
#     # 步骤3：绘制温度场等高线填充图（hot色图，红色=高温，黑色=低温）
#     im = ax.contourf(x, y, T_middle, cmap='hot')
#
#     # 步骤4：添加颜色条（标注温度单位为K）
#     plt.colorbar(im, label='温度 (K)')
#
#     # 步骤5：设置图形样式和标签
#     ax.set_title(f'{cutter_traj_type}轨迹相配合激光温度场分布')
#     ax.set_xlabel('X (m)')
#     ax.set_ylabel('Y (m)')
#
#     # 步骤6：调整布局并返回Figure对象
#     plt.tight_layout()
#     return fig
