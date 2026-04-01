"""
激光辅助加工路径可视化模块
核心功能：
1. 静态绘图：刀具轨迹、激光轨迹、温度场分布
2. 动态绘图：温度场动画播放/暂停/重置/保存
3. 辅助功能：Matplotlib图形转Qt控件显示
"""

# ============================== 导入模块区（按功能分组）==============================
# 1. 标准库模块
import os
import traceback
from io import BytesIO

# 2. 第三方数值计算/可视化模块
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)

# 3. PyQt5 GUI相关模块
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QSizePolicy
)

# -------------------- 新增：Matplotlib Qt 交互核心库 --------------------，激光轨迹绘制
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# -------------------- 新增：Qt 窗口基础库 --------------------
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication
import sys

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
def cutter_matplotlib_plot(x, y, Ret, cutter_traj_type, x_scope, y_scope):
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
    ax.plot(x, y, 'b-', linewidth=2, label=cutter_traj_type)

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
        (x[0], y[0]), Ret,  # 圆心坐标 + 半径
        color='#D6009B', alpha=0.6,  # 颜色（紫红色）+ 透明度
        label='刀具起点'  # 图例标签
    )
    ax.add_patch(start_circle)

    # 终点：青绿色半透明圆 + 黑色X标记
    end_circle = Circle(
        (x[-1], y[-1]), Ret,  # 圆心坐标 + 半径
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
    ax.set_title(f'{cutter_traj_type}型刀具轨迹')  # 图形标题
    ax.set_aspect('equal')  # 等比例坐标轴（保证圆形显示为正圆）
    ax.grid(True)  # 显示网格线

    # 步骤7：创建去重后的图例（避免重复标签）
    unique_labels = []
    unique_handles = []
    # 手动构建图例句柄（轨迹线 + 起点圆 + 终点圆）
    legend_items = [
        (Line2D([0], [0], color='b', linewidth=2, label=cutter_traj_type), cutter_traj_type),
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


def laser_matplotlib_plot(x_cutter, y_cutter, Ret, rb0, x_laser=None, y_laser=None, cutter_traj_type="line", x_scope=None, y_scope=None):
    """
    绘制刀具+激光轨迹对比静态图
    参数：
        x_cutter/y_cutter: 刀具轨迹X/Y坐标数组 (m)
        Ret: 刀具半径 (m)
        rb0: 激光光斑半径 (m)
        x_laser/y_laser: 激光轨迹X/Y坐标数组（可选，None则只绘制刀具轨迹）
        cutter_traj_type: 轨迹类型字符串（如"line"/"sin"/"zigzag"）
    参数新增：
        x_scope: X轴显示范围，格式为[X下限, X上限]（如[-Lx/2, Lx/2]）
        y_scope: Y轴显示范围，格式为[Y下限, Y上限]（如[-Ly/2, Ly/2]）
    返回：
        fig: Matplotlib的Figure对象（包含绘制好的对比图）
    绘制逻辑：
        1. 参数类型转换（确保所有参数为浮点型，避免绘图错误）
        2. 创建画布和坐标轴
        3. 绘制刀具轨迹（基础）
        4. 若提供激光轨迹，绘制激光轨迹
        5. 计算全局坐标轴范围（包含刀具+激光）
        6. 设置图形样式（标题、标签、图例、网格）
        7. 调整布局并返回Figure对象
    """
    # 步骤1：参数类型安全转换（避免不同类型导致的绘图错误）
    Ret = float(Ret)  # 刀具半径转浮点型
    rb0 = float(rb0)  # 激光光斑半径转浮点型
    x_cutter = np.array(x_cutter, dtype=float)  # 刀具X坐标转numpy浮点数组
    y_cutter = np.array(y_cutter, dtype=float)  # 刀具Y坐标转numpy浮点数组

    # 步骤2：创建绘图画布（8x6英寸）
    fig, ax = plt.subplots(figsize=(8, 6))

    # 步骤3：绘制刀具轨迹（蓝色实线，2px宽度）
    ax.plot(x_cutter, y_cutter, 'b-', linewidth=2, label="刀具轨迹")

    # 步骤4：绘制刀具起点/终点（圆形）
    # 刀具起点：紫红色半透明圆 + 黑色X标记
    cutter_start_circle = Circle(
        (x_cutter[0], y_cutter[0]), Ret,
        color='#D6009B', alpha=0.6, label='刀具起点'
    )
    ax.add_patch(cutter_start_circle)

    # 刀具终点：青绿色半透明圆 + 黑色X标记
    cutter_end_circle = Circle(
        (x_cutter[-1], y_cutter[-1]), Ret,
        color='#00C1B3', alpha=0.6, label='刀具终点'
    )
    ax.add_patch(cutter_end_circle)

    # 刀具起点/终点中心X标记
    ax.scatter(
        [float(x_cutter[0]), float(x_cutter[-1])],
        [float(y_cutter[0]), float(y_cutter[-1])],
        color=['black', 'black'], s=20, marker='x', zorder=10
    )

    # 步骤5：如果提供激光轨迹，绘制激光轨迹
    laser_plotted = False
    if x_laser is not None and y_laser is not None:
        laser_plotted = True

        # 激光轨迹坐标转换为浮点型
        if hasattr(x_laser, '__len__'):
            x_laser = np.array(x_laser, dtype=float)
            y_laser = np.array(y_laser, dtype=float)
        else:
            x_laser = float(x_laser)
            y_laser = float(y_laser)

        # 绘制激光轨迹线（黄色虚线，1.5px宽度，0.7透明度）
        ax.plot(x_laser, y_laser, 'y--', linewidth=1.5, alpha=0.7, label='激光轨迹')

        # 确定激光起点/终点坐标
        if hasattr(x_laser, '__len__'):
            laser_start_x, laser_start_y = float(x_laser[0]), float(y_laser[0])
            laser_end_x, laser_end_y = float(x_laser[-1]), float(y_laser[-1])
        else:
            laser_start_x = laser_end_x = float(x_laser)
            laser_start_y = laser_end_y = float(y_laser)

        # 绘制激光起点（橙色半透明圆 + 黑色+标记）
        laser_start_circle = Circle(
            (laser_start_x, laser_start_y), float(rb0),
            color='#FF6B35', alpha=0.6, label='激光起点'
        )
        ax.add_patch(laser_start_circle)

        # 绘制激光终点（紫色半透明圆 + 黑色+标记）
        laser_end_circle = Circle(
            (laser_end_x, laser_end_y), float(rb0),
            color='#7A4FFF', alpha=0.6, label='激光终点'
        )
        ax.add_patch(laser_end_circle)

        # 激光起点/终点中心+标记
        ax.scatter(
            [laser_start_x, laser_end_x],
            [laser_start_y, laser_end_y],
            color=['black', 'black'], s=10, marker='+', zorder=10
        )

    # 步骤6：
    # ========== 核心修改：删除原有自动计算范围的逻辑，替换为指定范围 ==========
    # 移除原有计算all_x/all_y、x_min/x_max、y_min/y_max、margin的代码
    # 直接使用用户指定的范围
    ax.set_xlim(x_scope[0], x_scope[1])  # X轴范围：用户指定
    ax.set_ylim(y_scope[0], y_scope[1])  # Y轴范围：用户指定

    # 步骤7：设置图形样式和标签
    ax.set_xlabel('X/m', fontsize=12)  # X轴标签（12号字体）
    ax.set_ylabel('Y/m', fontsize=12)  # Y轴标签（12号字体）
    ax.set_aspect('equal')  # 等比例坐标轴
    ax.grid(True, linestyle='--', alpha=0.5)  # 网格线（虚线，0.5透明度）
    ax.ticklabel_format(style='sci', axis='both', scilimits=(0, 0))  # 科学计数法显示坐标

    # 步骤8：设置图形标题（根据是否绘制激光轨迹调整）
    if laser_plotted:
        ax.set_title(f'刀具与激光轨迹', fontsize=14, fontweight='bold')
    else:
        ax.set_title(f'刀具轨迹', fontsize=14, fontweight='bold')

    # 步骤9：创建去重后的图例（按固定顺序，避免重复）
    legend_items = [
        (Line2D([0], [0], color='b', linewidth=2, label='刀具轨迹'), '刀具轨迹'),
        (cutter_start_circle, '刀具起点'),
        (cutter_end_circle, '刀具终点')
    ]

    if laser_plotted:
        legend_items.extend([
            (Line2D([0], [0], color='y', linewidth=1.5, alpha=0.7, linestyle='--', label='激光轨迹'), '激光轨迹'),
            (laser_start_circle, '激光起点'),
            (laser_end_circle, '激光终点')
        ])

    # 去重逻辑
    seen_labels = set()
    unique_handles = []
    unique_labels = []
    for handle, label in legend_items:
        if label not in seen_labels:
            seen_labels.add(label)
            unique_handles.append(handle)
            unique_labels.append(label)

    # ❌ 原代码：ax.legend(unique_handles, unique_labels, loc='best', fontsize=10)
    # 修改为【右侧纵向图例】，永不遮挡图形
    ax.legend(
        unique_handles, unique_labels,
        loc='center left',  # 图例垂直居中对齐
        bbox_to_anchor=(1.02, 0.5),  # 锚点：放在图**右侧外部**
        fontsize=10,
        ncol=1,  # 单列纵向排列
        borderaxespad=0,  # 无多余边距
        frameon=True  # 保留图例边框，更清晰
    )
    # 步骤10：调整布局并返回Figure对象
    plt.tight_layout()
    return fig




def heat_even_matplotlib_plot(x, y, nz, T, cutter_traj_type):
    """
    绘制等弧长算法温度场二维切片图（z方向中间层）
    参数：
        x: X轴坐标数组 (m)
        y: Y轴坐标数组 (m)
        nz: Z方向网格数量
        T: 温度场三维数组 (nx × ny × nz)，单位K
        cutter_traj_type: 轨迹类型字符串（如"line"/"sin"/"zigzag"）
    返回：
        fig: Matplotlib的Figure对象（包含温度场分布图）
    绘制逻辑：
        与普通温度场绘图逻辑一致，差异点：
        1. 温度数据需要转置（T[:, :, nz//2].T）以适配等弧长算法的数据格式
        2. 等高线层级设置为100层（更精细的温度梯度）
        3. 标题标注"均匀温度场"
    """
    # 步骤1：创建绘图画布（8x6英寸）
    fig, ax = plt.subplots(figsize=(8, 6))

    # 步骤2：提取z方向中间层温度数据并转置（适配等弧长算法数据格式）
    T_middle = T[:, :, nz // 2].T  # 中间层温度数据 + 转置

    # 步骤3：绘制温度场等高线填充图（100层，hot色图）
    im = ax.contourf(x, y, T_middle, 100, cmap='hot')

    # 步骤4：添加颜色条（标注温度单位为K）
    plt.colorbar(im, label='温度 (K)')

    # 步骤5：设置图形样式和标签
    ax.set_title(f'{cutter_traj_type}轨迹相配合激光均匀温度场分布')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')

    # 步骤6：调整布局并返回Figure对象
    plt.tight_layout()
    return fig


# ============================== 动态动画类（温度场）=============================
class HeatAnimationController:
    """
    温度场动画控制器类
    核心功能：
        1. 初始化动画画布和定时器
        2. 播放/暂停/重置动画
        3. 保存动画为GIF/MP4文件
        4. 清理动画资源
    设计思路：
        - 封装动画的所有操作，对外提供简单的play/pause/reset/save接口
        - 内部通过QTimer实现帧更新，避免阻塞UI线程
        - 适配Qt控件的大小和布局，保证动画显示效果
    """

    def __init__(self, container, x, y, animation_frames, animation_frame_times, traj_type):
        """
        初始化动画控制器
        参数：
            container: Qt容器控件（如QWidget），用于显示动画画布
            x: X轴坐标数组 (m)
            y: Y轴坐标数组 (m)
            animation_frames: 温度场帧列表（每个元素是二维温度数组）
            animation_frame_times: 帧对应的时间数组 (s)
            traj_type: 轨迹类型字符串（如"line"/"sin"/"zigzag"）
        初始化逻辑：
            1. 保存输入参数
            2. 清空容器控件原有内容
            3. 创建Matplotlib画布并添加到容器
            4. 计算温度数据范围（用于色图归一化）
            5. 创建初始温度场图像
            6. 设置动画样式（颜色条、标签、标题）
            7. 创建定时器并绑定帧更新函数
            8. 绘制初始帧
        """
        # 步骤1：保存输入参数
        self.container = container  # Qt容器控件
        self.x = x  # X轴坐标
        self.y = y  # Y轴坐标
        self.animation_frames = animation_frames  # 温度场帧列表
        self.animation_frame_times = animation_frame_times  # 帧时间数组
        self.traj_type = traj_type  # 轨迹类型
        self.timer = None  # 动画定时器
        self.canvas = None  # Matplotlib画布
        self.current_frame = 0  # 当前帧索引
        self.is_playing = False  # 动画播放状态
        self.vmin = 0  # 温度最小值（色图归一化）
        self.vmax = 1  # 温度最大值（色图归一化）
        self.im = None  # 温度场图像对象
        self.cbar = None  # 颜色条对象
        self.extent = None  # 图像显示范围

        # 步骤2：清空容器控件原有内容（避免重叠）
        if container.layout():
            while container.layout().count():
                item = container.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        try:
            # 步骤3：创建Matplotlib画布（适配560x420容器的大小）
            dpi = 80  # 分辨率
            fig_width = 560 / dpi  # 画布宽度 = 容器宽度 / DPI
            fig_height = 420 / dpi  # 画布高度 = 容器高度 / DPI
            self.fig, self.ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

            # 创建Qt兼容的画布并设置大小策略（自适应容器）
            self.canvas = FigureCanvas(self.fig)
            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # 将画布添加到容器控件
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)  # 去除布局边距
            layout.setSpacing(0)  # 去除控件间距
            layout.addWidget(self.canvas)

            # 步骤4：计算温度数据范围（用于色图归一化，避免帧间颜色跳变）
            try:
                # 转换为numpy数组并展平所有帧数据
                if not isinstance(animation_frames, np.ndarray):
                    animation_frames = np.array(animation_frames)

                all_data = []
                for frame in animation_frames:
                    if frame.ndim == 2:
                        all_data.append(frame.T.flatten())
                    else:
                        all_data.append(frame.flatten())
                all_data = np.concatenate(all_data)

                # 过滤NaN值，使用有效数据计算范围
                valid_data = all_data[~np.isnan(all_data)]
                if len(valid_data) == 0:
                    self.vmin, self.vmax = 0, 1  # 默认范围
                    print("警告: 温度数据全为NaN，使用默认范围[0,1]")
                else:
                    self.vmin, self.vmax = np.min(valid_data), np.max(valid_data)
                    # 若所有值相同，设置小范围保证色图显示
                    if self.vmin == self.vmax:
                        self.vmin -= 0.1 if self.vmin != 0 else -0.1
                        self.vmax += 0.1 if self.vmax != 0 else 0.1
            except Exception as e:
                print(f"计算温度数据范围失败: {e}")
                self.vmin, self.vmax = 0, 1  # 降级使用默认范围

            # 步骤5：创建初始温度场图像
            try:
                # 计算图像显示范围
                x_min, x_max = np.min(x), np.max(x)
                y_min, y_max = np.min(y), np.max(y)
                # 防止范围为0导致绘图错误
                if x_min == x_max:
                    x_min, x_max = x_min - 0.1, x_max + 0.1
                if y_min == y_max:
                    y_min, y_max = y_min - 0.1, y_max + 0.1
                self.extent = [x_min, x_max, y_min, y_max]

                # 处理第一帧数据（确保二维）
                first_frame = animation_frames[0]
                if first_frame.ndim == 1:
                    first_frame = first_frame.reshape(-1, 1)

                # 创建imshow图像（hot色图，归一化到温度范围）
                self.im = self.ax.imshow(
                    first_frame.T,  # 温度数据（转置）
                    extent=self.extent,  # 显示范围
                    origin='lower',  # 原点在左下角
                    cmap='hot',  # 热图色表
                    vmin=self.vmin, vmax=self.vmax,  # 归一化范围
                    aspect='auto',  # 自动适配宽高比
                    interpolation='nearest'  # 最近邻插值（保持温度精度）
                )
            except Exception as e:
                print(f"创建初始温度场图像失败: {e}")
                # 降级创建空图像
                self.im = self.ax.imshow(np.zeros((10, 10)), cmap='hot', vmin=0, vmax=1)

            # 步骤6：设置动画样式
            # 添加颜色条（紧凑布局，适配小容器）
            try:
                self.cbar = self.fig.colorbar(
                    self.im, ax=self.ax, label='温度 (K)',
                    fraction=0.05, pad=0.03  # 紧凑布局参数
                )
                self.cbar.ax.tick_params(labelsize=6)  # 缩小刻度标签
            except:
                self.cbar = None  # 颜色条创建失败则忽略

            # 设置坐标轴标签（小字体适配容器）
            self.ax.set_xlabel('X/m', fontsize=8)
            self.ax.set_ylabel('Y/m', fontsize=8)

            # 设置初始标题（显示第一帧时间）
            title_text = f'温度场分布 (时间: {animation_frame_times[0]:.4f} s)'
            self.ax.set_title(title_text, fontsize=9, pad=5)

            # 缩小坐标轴刻度标签
            self.ax.tick_params(axis='both', labelsize=6)

            # 手动调整布局（避免自动布局导致的显示问题）
            left_margin = 0.12  # 左边距
            right_margin = 0.82 if self.cbar else 0.92  # 右边距（有颜色条则留空间）
            bottom_margin = 0.15  # 底部边距
            top_margin = 0.92  # 顶部边距
            self.fig.subplots_adjust(
                left=left_margin, right=right_margin,
                bottom=bottom_margin, top=top_margin,
                wspace=0, hspace=0
            )

            # 步骤7：创建动画定时器（每200ms更新一帧）
            self.timer = QTimer()
            self.timer.timeout.connect(self._update_frame)

            # 步骤8：绘制初始帧
            self.canvas.draw()
            self.canvas.updateGeometry()

        except Exception as e:
            print(f"初始化动画控制器失败: {e}")
            traceback.print_exc()

    def _update_frame(self):
        """
        内部帧更新函数（定时器触发）
        更新逻辑：
            1. 循环更新帧索引（到最后一帧则回到第一帧）
            2. 更新温度场图像数据
            3. 更新标题（显示当前帧时间）
            4. 重绘画布
        """
        try:
            # 循环帧索引
            if self.current_frame >= len(self.animation_frames):
                self.current_frame = 0

            # 获取当前帧数据并确保二维
            frame_data = self.animation_frames[self.current_frame]
            if frame_data.ndim == 1:
                frame_data = frame_data.reshape(-1, 1)

            # 更新图像数据
            self.im.set_data(frame_data.T)

            # 更新标题（显示当前时间）
            time_str = f"{self.animation_frame_times[self.current_frame]:.4f}"
            self.ax.set_title(f'温度场分布 (时间: {time_str} s)', fontsize=9, pad=5)

            # 重绘画布
            self.canvas.draw()

            # 帧索引+1
            self.current_frame += 1

        except Exception as e:
            print(f"更新动画帧失败: {e}")
            # 出错则停止定时器
            if self.timer and self.timer.isActive():
                self.timer.stop()

    def play(self):
        """
        播放动画
        逻辑：
            1. 检查定时器是否有效
            2. 若当前在最后一帧，重置到第一帧
            3. 启动定时器（200ms/帧）
            4. 更新播放状态
        """
        if self.timer and not self.is_playing:
            # 重置到第一帧（如果在最后）
            if self.current_frame >= len(self.animation_frames):
                self.current_frame = 0
            # 启动定时器（200ms更新一次）
            self.timer.start(200)
            self.is_playing = True

    def pause(self):
        """
        暂停动画
        逻辑：
            1. 检查定时器是否有效且正在播放
            2. 停止定时器
            3. 更新播放状态
        """
        if self.timer and self.is_playing:
            self.timer.stop()
            self.is_playing = False

    def reset(self):
        """
        重置动画到第一帧
        逻辑：
            1. 重置帧索引到0
            2. 更新图像数据为第一帧
            3. 更新标题为第一帧时间
            4. 重绘画布
            5. 暂停动画
        """
        self.current_frame = 0

        try:
            # 更新第一帧数据
            first_frame = self.animation_frames[0]
            if first_frame.ndim == 1:
                first_frame = first_frame.reshape(-1, 1)
            self.im.set_data(first_frame.T)

            # 更新标题
            time_str = f"{self.animation_frame_times[0]:.4f}"
            self.ax.set_title(f'温度场分布 (时间: {time_str} s)', fontsize=9, pad=5)

            # 重绘画布
            self.canvas.draw()
        except Exception as e:
            print(f"重置动画失败: {e}")

        # 暂停动画
        if self.timer and self.is_playing:
            self.timer.stop()
            self.is_playing = False

    def save(self, parent_widget=None):
        """
        保存动画为GIF/MP4文件
        参数：
            parent_widget: 父窗口控件（用于文件对话框的父窗口）
        返回：
            bool: 保存成功返回True，失败返回False
        保存逻辑：
            1. 检查动画数据是否有效
            2. 弹出文件保存对话框（支持GIF/MP4）
            3. 创建新的Matplotlib画布用于保存
            4. 生成FuncAnimation对象
            5. 保存文件并清理资源
        """
        # 检查动画数据
        if not self.animation_frames or not self.animation_frame_times:
            return False

        try:
            # 弹出文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "保存动画",
                "",
                "GIF文件 (*.gif);;MP4文件 (*.mp4);;所有文件 (*.*)"
            )

            if not file_path:
                return False  # 用户取消保存

            # 自动补充文件扩展名
            if not file_path.endswith('.gif') and not file_path.endswith('.mp4'):
                file_path += '.gif'

            # 创建新画布用于保存（不显示）
            save_fig, save_ax = plt.subplots(figsize=(8, 6))

            # 创建保存用的温度场图像
            save_im = save_ax.imshow(
                self.animation_frames[0].T,
                extent=self.extent,
                origin='lower',
                cmap='hot',
                vmin=self.vmin, vmax=self.vmax,
                aspect='auto',
                interpolation='nearest'
            )

            # 添加颜色条和标签
            save_fig.colorbar(save_im, ax=save_ax, label='温度 (K)')
            save_ax.set_xlabel('X/m')
            save_ax.set_ylabel('Y/m')
            save_ax.set_title(f'{self.traj_type}轨迹温度场分布')

            # 定义帧更新函数
            def update_save_frame(frame_idx):
                save_im.set_data(self.animation_frames[frame_idx].T)
                time_str = f"{self.animation_frame_times[frame_idx]:.4f}"
                save_ax.set_title(f'{self.traj_type}轨迹温度场分布 (时间: {time_str} s)')
                return save_im,

            # 创建FuncAnimation对象
            num_frames = len(self.animation_frames)
            ani = FuncAnimation(
                save_fig,
                update_save_frame,
                frames=num_frames,
                interval=200,
                blit=True
            )

            # 保存文件
            if file_path.endswith('.gif'):
                ani.save(file_path, writer='pillow', fps=5, dpi=100)
            elif file_path.endswith('.mp4'):
                ani.save(file_path, writer='ffmpeg', fps=5, dpi=100)

            # 清理资源
            plt.close(save_fig)

            return True

        except Exception as e:
            print(f"保存动画失败: {e}")
            traceback.print_exc()
            return False

    def close(self):
        """
        清理动画资源（防止内存泄漏）
        逻辑：
            1. 停止定时器
            2. 删除画布控件
            3. 置空属性
        """
        # 停止定时器
        if self.timer and self.timer.isActive():
            self.timer.stop()
            self.timer = None

        # 删除画布
        if self.canvas:
            self.canvas.deleteLater()
            self.canvas = None


# ============================== 动画创建工具函数 ==============================
def create_simple_heat_animation(container, x, y, animation_frames, animation_frame_times, traj_type):
    """
    简化的动画创建函数（封装异常处理）
    参数：
        同HeatAnimationController.__init__
    返回：
        controller: HeatAnimationController对象（成功）/None（失败）
    """
    try:
        # 创建动画控制器
        controller = HeatAnimationController(
            container, x, y,
            animation_frames, animation_frame_times,
            traj_type
        )
        return controller
    except Exception as e:
        print(f"创建温度场动画失败: {e}")
        traceback.print_exc()
        return None

# 交互式绘图控件类
class InteractiveMatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. 强制设置零边距布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0) # 消除控件自身边距
        self._layout.setSpacing(0)

        self.canvas = None
        self.toolbar = None

    def set_figure(self, fig):
        # 2. 清理旧控件
        if self.canvas:
            self._layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
        if self.toolbar:
            self._layout.removeWidget(self.toolbar)
            self.toolbar.deleteLater()

        # 3. 核心修复：移除默认的tight_layout，改用 subplots_adjust 精确控制
        fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.08) # 收紧边缘，消除大白边

        # 4. 新建画布和工具栏
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # 5. 添加到布局
        self._layout.addWidget(self.toolbar)
        self._layout.addWidget(self.canvas)

        # 6. 强制刷新
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
