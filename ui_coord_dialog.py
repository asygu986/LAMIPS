# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'coord_dialogqArqxo.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtWidgets import QDialog, QMessageBox, QDoubleSpinBox
from PyQt5.uic import loadUi


class CoordInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 加载UI文件
        loadUi(r'D:\PythonProjects\Pycharm\Graduate_design\UI\coord_dialog.ui', self)
        self.setWindowTitle("铣刀路径点输入窗口")

        # 连接信号槽
        self.btn_add_row.clicked.connect(self.add_row)
        self.btn_delete_row.clicked.connect(self.delete_row)
        self.btn_clear_table.clicked.connect(self.clear_table)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # 存储临时坐标
        self.temp_coordinates = []

        # 重要：先不初始化表格，等待 set_coordinates 调用
        # 或者如果有默认坐标，在这里初始化
        self.tableWidget_coords.setRowCount(0)
        # 暂时不添加空行，等 set_coordinates 方法调用

    def set_coordinates(self, coordinates):
        """设置初始坐标数据"""
        # print(f"设置坐标：收到 {len(coordinates)} 个坐标点")

        # 清空临时存储
        self.temp_coordinates = []

        # 验证坐标数据
        if coordinates and isinstance(coordinates, list):
            self.temp_coordinates = coordinates.copy()
            # print(f"复制了 {len(self.temp_coordinates)} 个坐标到临时存储")
        else:
            print("坐标数据无效或为空")
            self.temp_coordinates = []

        # 加载到表格
        self.load_coordinates_to_table()

    def load_coordinates_to_table(self):
        """将坐标数据加载到表格中"""
        # print(f"加载坐标到表格：{len(self.temp_coordinates)} 个点")

        # 清空表格
        self.tableWidget_coords.setRowCount(0)

        # 如果有保存的坐标，加载它们
        if self.temp_coordinates:
            # print(f"正在加载 {len(self.temp_coordinates)} 个坐标点到表格...")

            for i, (x, y) in enumerate(self.temp_coordinates):
                row = self.tableWidget_coords.rowCount()
                self.tableWidget_coords.insertRow(row)

                # 设置单元格编辑器
                self.set_cell_editor(row, 0)
                self.set_cell_editor(row, 1)

                # 获取单元格控件并设置值
                x_widget = self.tableWidget_coords.cellWidget(row, 0)
                y_widget = self.tableWidget_coords.cellWidget(row, 1)

                if x_widget:
                    x_widget.setValue(float(x))
                if y_widget:
                    y_widget.setValue(float(y))

                print(f"  加载点{i + 1}: ({x:.6f}, {y:.6f})")
        else:
            print("没有坐标数据，添加一个空行")
            # 如果没有坐标，添加一个空行
            self.add_row()

    def set_cell_editor(self, row, col):
        """为单元格设置数字输入框"""
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(3)  # 6位小数
        spin_box.setRange(-10, 10)  # 根据实际情况调整范围
        spin_box.setSingleStep(0.001)  # 添加上下三角步长为0.001
        spin_box.setValue(0.0)
        self.tableWidget_coords.setCellWidget(row, col, spin_box)
        return spin_box  # 返回控件引用

    def add_row(self):
        """添加新行"""
        row_count = self.tableWidget_coords.rowCount()
        self.tableWidget_coords.insertRow(row_count)

        # 获取并返回控件引用
        x_widget = self.set_cell_editor(row_count, 0)
        y_widget = self.set_cell_editor(row_count, 1)

        return x_widget, y_widget

    def delete_row(self):
        """删除选中行"""
        current_row = self.tableWidget_coords.currentRow()
        if current_row >= 0:
            self.tableWidget_coords.removeRow(current_row)
        else:
            QMessageBox.warning(self, "警告", "请先选择要删除的行")

    def clear_table(self):
        """清空表格"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有数据吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tableWidget_coords.setRowCount(0)
            # 清空后添加一个空行
            self.add_row()

    def get_coordinates(self):
        """获取所有坐标点"""
        coordinates = []
        row_count = self.tableWidget_coords.rowCount()

        # print(f"获取坐标：表格有 {row_count} 行")

        for row in range(row_count):
            x_widget = self.tableWidget_coords.cellWidget(row, 0)
            y_widget = self.tableWidget_coords.cellWidget(row, 1)

            if x_widget and y_widget:
                try:
                    x = x_widget.value()
                    y = y_widget.value()

                    # 记录所有行，包括0值
                    coordinates.append((x, y))
                    # print(f"  第{row + 1}行: ({x:.6f}, {y:.6f})")

                except Exception as e:
                    print(f"  第{row + 1}行读取错误: {e}")
                    # 如果读取失败，跳过这行
            else:
                print(f"  第{row + 1}行: 控件不存在")

        # print(f"总共获取到 {len(coordinates)} 个有效坐标点")
        return coordinates