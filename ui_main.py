# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_mainmqdnxR.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from plot_disp import InteractiveMatplotlibWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(2112, 1015)
        self.actionsave = QAction(MainWindow)
        self.actionsave.setObjectName(u"actionsave")
        self.actionload = QAction(MainWindow)
        self.actionload.setObjectName(u"actionload")
        self.actiontool = QAction(MainWindow)
        self.actiontool.setObjectName(u"actiontool")
        self.actioninformation = QAction(MainWindow)
        self.actioninformation.setObjectName(u"actioninformation")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.Input = QFrame(self.centralwidget)
        self.Input.setObjectName(u"Input")
        self.Input.setMaximumSize(QSize(16777215, 16777215))
        self.Input.setStyleSheet(u"QFrame{\n"
"	background-color:rgb(221, 221, 221)\n"
"}")
        self.Input.setFrameShape(QFrame.StyledPanel)
        self.Input.setFrameShadow(QFrame.Raised)
        self.label_hand = QLabel(self.Input)
        self.label_hand.setObjectName(u"label_hand")
        self.label_hand.setGeometry(QRect(10, 20, 72, 15))
        font = QFont()
        font.setFamily(u"Agency FB")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_hand.setFont(font)
        self.label_Gcode = QLabel(self.Input)
        self.label_Gcode.setObjectName(u"label_Gcode")
        self.label_Gcode.setGeometry(QRect(10, 450, 72, 15))
        font1 = QFont()
        font1.setFamily(u"Agency FB")
        font1.setBold(True)
        font1.setWeight(75)
        self.label_Gcode.setFont(font1)
        self.line_3 = QFrame(self.Input)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setGeometry(QRect(10, 60, 531, 21))
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)
        self.line_4 = QFrame(self.Input)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setGeometry(QRect(10, 420, 531, 21))
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)
        self.label = QLabel(self.Input)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 80, 81, 16))
        font2 = QFont()
        font2.setFamily(u"Adobe Arabic")
        font2.setBold(True)
        font2.setItalic(True)
        font2.setWeight(75)
        self.label.setFont(font2)
        self.label_2 = QLabel(self.Input)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(10, 220, 81, 16))
        self.label_2.setFont(font2)
        self.label_3 = QLabel(self.Input)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 150, 81, 16))
        self.label_3.setFont(font2)
        self.line_5 = QFrame(self.Input)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setGeometry(QRect(80, 70, 20, 31))
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)
        self.label_5 = QLabel(self.Input)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(120, 150, 72, 15))
        self.label_6 = QLabel(self.Input)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(480, 150, 72, 15))
        self.label_7 = QLabel(self.Input)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(300, 150, 72, 15))
        self.label_8 = QLabel(self.Input)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(120, 220, 72, 15))
        self.label_9 = QLabel(self.Input)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(300, 220, 72, 15))
        self.label_11 = QLabel(self.Input)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(300, 80, 71, 16))
        self.label_14 = QLabel(self.Input)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setGeometry(QRect(120, 80, 61, 16))
        self.comboBox_trajectory_type = QComboBox(self.Input)
        self.comboBox_trajectory_type.addItem("")
        self.comboBox_trajectory_type.addItem("")
        self.comboBox_trajectory_type.addItem("")
        self.comboBox_trajectory_type.setObjectName(u"comboBox_trajectory_type")
        self.comboBox_trajectory_type.setGeometry(QRect(190, 290, 81, 22))
        self.stackedWidget_params = QStackedWidget(self.Input)
        self.stackedWidget_params.setObjectName(u"stackedWidget_params")
        self.stackedWidget_params.setGeometry(QRect(110, 320, 431, 81))
        self.page_line = QWidget()
        self.page_line.setObjectName(u"page_line")
        self.stackedWidget_params.addWidget(self.page_line)
        self.page_sin = QWidget()
        self.page_sin.setObjectName(u"page_sin")
        self.lineEdit_sinFrequency = QLineEdit(self.page_sin)
        self.lineEdit_sinFrequency.setObjectName(u"lineEdit_sinFrequency")
        self.lineEdit_sinFrequency.setGeometry(QRect(80, 20, 71, 21))
        self.label_18 = QLabel(self.page_sin)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setGeometry(QRect(10, 20, 72, 15))
        self.label_19 = QLabel(self.page_sin)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setGeometry(QRect(190, 20, 72, 15))
        self.lineEdit_sinAmplitude = QLineEdit(self.page_sin)
        self.lineEdit_sinAmplitude.setObjectName(u"lineEdit_sinAmplitude")
        self.lineEdit_sinAmplitude.setGeometry(QRect(260, 20, 71, 21))
        self.stackedWidget_params.addWidget(self.page_sin)
        self.page_zigzag = QWidget()
        self.page_zigzag.setObjectName(u"page_zigzag")
        self.lineEdit_num_zigzags = QLineEdit(self.page_zigzag)
        self.lineEdit_num_zigzags.setObjectName(u"lineEdit_num_zigzags")
        self.lineEdit_num_zigzags.setGeometry(QRect(90, 20, 81, 21))
        self.label_21 = QLabel(self.page_zigzag)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setGeometry(QRect(10, 20, 81, 16))
        self.label_22 = QLabel(self.page_zigzag)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setGeometry(QRect(10, 50, 81, 16))
        self.label_23 = QLabel(self.page_zigzag)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setGeometry(QRect(190, 50, 81, 16))
        self.lineEdit_amplitude_zigzag = QLineEdit(self.page_zigzag)
        self.lineEdit_amplitude_zigzag.setObjectName(u"lineEdit_amplitude_zigzag")
        self.lineEdit_amplitude_zigzag.setGeometry(QRect(90, 50, 81, 21))
        self.lineEdit_offset = QLineEdit(self.page_zigzag)
        self.lineEdit_offset.setObjectName(u"lineEdit_offset")
        self.lineEdit_offset.setGeometry(QRect(270, 50, 81, 21))
        self.label_24 = QLabel(self.page_zigzag)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setGeometry(QRect(190, 20, 81, 16))
        self.lineEdit_period = QLineEdit(self.page_zigzag)
        self.lineEdit_period.setObjectName(u"lineEdit_period")
        self.lineEdit_period.setGeometry(QRect(270, 20, 81, 21))
        self.stackedWidget_params.addWidget(self.page_zigzag)
        self.label_16 = QLabel(self.Input)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setGeometry(QRect(120, 290, 61, 16))
        self.lineEdit_Det = QLineEdit(self.Input)
        self.lineEdit_Det.setObjectName(u"lineEdit_Det")
        self.lineEdit_Det.setGeometry(QRect(370, 80, 71, 21))
        self.lineEdit_nC = QLineEdit(self.Input)
        self.lineEdit_nC.setObjectName(u"lineEdit_nC")
        self.lineEdit_nC.setGeometry(QRect(190, 80, 71, 21))
        self.lineEdit_k = QLineEdit(self.Input)
        self.lineEdit_k.setObjectName(u"lineEdit_k")
        self.lineEdit_k.setGeometry(QRect(190, 150, 71, 21))
        self.lineEdit_cp = QLineEdit(self.Input)
        self.lineEdit_cp.setObjectName(u"lineEdit_cp")
        self.lineEdit_cp.setGeometry(QRect(540, 150, 81, 21))
        self.lineEdit_rho = QLineEdit(self.Input)
        self.lineEdit_rho.setObjectName(u"lineEdit_rho")
        self.lineEdit_rho.setGeometry(QRect(370, 150, 71, 21))
        self.lineEdit_source_power = QLineEdit(self.Input)
        self.lineEdit_source_power.setObjectName(u"lineEdit_source_power")
        self.lineEdit_source_power.setGeometry(QRect(190, 220, 71, 21))
        self.lineEdit_rb0 = QLineEdit(self.Input)
        self.lineEdit_rb0.setObjectName(u"lineEdit_rb0")
        self.lineEdit_rb0.setGeometry(QRect(370, 220, 71, 21))
        self.btn_open_coords = QPushButton(self.Input)
        self.btn_open_coords.setObjectName(u"btn_open_coords")
        self.btn_open_coords.setGeometry(QRect(10, 340, 91, 41))
        self.label_4 = QLabel(self.Input)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 290, 81, 16))
        self.label_4.setFont(font2)
        self.line_8 = QFrame(self.Input)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setGeometry(QRect(10, 270, 81, 16))
        self.line_8.setFrameShape(QFrame.HLine)
        self.line_8.setFrameShadow(QFrame.Sunken)
        self.line_9 = QFrame(self.Input)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setGeometry(QRect(10, 130, 81, 16))
        self.line_9.setFrameShape(QFrame.HLine)
        self.line_9.setFrameShadow(QFrame.Sunken)
        self.layoutWidget = QWidget(self.Input)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(70, 800, 481, 41))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_cutter = QPushButton(self.layoutWidget)
        self.btn_cutter.setObjectName(u"btn_cutter")
        self.btn_cutter.setStyleSheet(u"QPushButton{\n"
"	background-color:rgb(0,174,236);\n"
"	height:22px;\n"
"\n"
"}\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.horizontalLayout.addWidget(self.btn_cutter)

        self.btn_laser = QPushButton(self.layoutWidget)
        self.btn_laser.setObjectName(u"btn_laser")
        self.btn_laser.setStyleSheet(u"QPushButton{\n"
"	background-color:rgb(246, 255, 144);\n"
"	height:22px;\n"
"\n"
"}\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.horizontalLayout.addWidget(self.btn_laser)

        self.btn_opt_laser = QPushButton(self.layoutWidget)
        self.btn_opt_laser.setObjectName(u"btn_opt_laser")
        self.btn_opt_laser.setStyleSheet(u"QPushButton{\n"
"	background-color:rgb(255, 97, 139);\n"
"	height:22px;\n"
"}\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.horizontalLayout.addWidget(self.btn_opt_laser)

        self.btn_heat_even = QPushButton(self.layoutWidget)
        self.btn_heat_even.setObjectName(u"btn_heat_even")
        self.btn_heat_even.setStyleSheet(u"QPushButton{\n"
"	background-color:rgb(255, 0, 0);\n"
"	height:22px;\n"
"}\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.horizontalLayout.addWidget(self.btn_heat_even)

        self.line_10 = QFrame(self.Input)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setGeometry(QRect(80, 140, 20, 31))
        self.line_10.setFrameShape(QFrame.VLine)
        self.line_10.setFrameShadow(QFrame.Sunken)
        self.line_11 = QFrame(self.Input)
        self.line_11.setObjectName(u"line_11")
        self.line_11.setGeometry(QRect(10, 200, 81, 16))
        self.line_11.setFrameShape(QFrame.HLine)
        self.line_11.setFrameShadow(QFrame.Sunken)
        self.line_12 = QFrame(self.Input)
        self.line_12.setObjectName(u"line_12")
        self.line_12.setGeometry(QRect(80, 210, 20, 31))
        self.line_12.setFrameShape(QFrame.VLine)
        self.line_12.setFrameShadow(QFrame.Sunken)
        self.btn_upload_gcode = QPushButton(self.Input)
        self.btn_upload_gcode.setObjectName(u"btn_upload_gcode")
        self.btn_upload_gcode.setGeometry(QRect(10, 540, 91, 41))
        self.btn_set_default = QPushButton(self.Input)
        self.btn_set_default.setObjectName(u"btn_set_default")
        self.btn_set_default.setGeometry(QRect(120, 10, 101, 41))
        self.btn_set_default.setStyleSheet(u"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")
        self.line_13 = QFrame(self.Input)
        self.line_13.setObjectName(u"line_13")
        self.line_13.setGeometry(QRect(80, 280, 20, 31))
        self.line_13.setFrameShape(QFrame.VLine)
        self.line_13.setFrameShadow(QFrame.Sunken)
        self.btn_clear_params = QPushButton(self.Input)
        self.btn_clear_params.setObjectName(u"btn_clear_params")
        self.btn_clear_params.setGeometry(QRect(300, 10, 101, 41))
        self.btn_clear_params.setStyleSheet(u"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")
        self.btn_interval_exec = QPushButton(self.Input)
        self.btn_interval_exec.setObjectName(u"btn_interval_exec")
        self.btn_interval_exec.setGeometry(QRect(10, 620, 91, 41))

        self.gridLayout.addWidget(self.Input, 0, 0, 1, 1)

        self.Status = QFrame(self.centralwidget)
        self.Status.setObjectName(u"Status")
        self.Status.setEnabled(True)
        self.Status.setMaximumSize(QSize(16777215, 94))
        self.Status.setStyleSheet(u"QFrame{\n"
"background-color:rgb(161, 194, 255)\n"
"}")
        self.Status.setFrameShape(QFrame.StyledPanel)
        self.Status.setFrameShadow(QFrame.Raised)
        self.textEdit_status = QTextEdit(self.Status)
        self.textEdit_status.setObjectName(u"textEdit_status")
        self.textEdit_status.setGeometry(QRect(10, 10, 681, 81))
        self.textEdit_status.setStyleSheet(u"QTextEdit {\n"
"    background-color: #f8f9fa;\n"
"    border: 1px solid #dee2e6;\n"
"    font-family: \"Consolas\", \"Monaco\", monospace;\n"
"    font-size: 9pt;\n"
"}")
        self.textEdit_status.setReadOnly(True)
        self.layoutWidget1 = QWidget(self.Status)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(780, 30, 295, 41))
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_2.setSpacing(10)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.checkBox_auto_scroll = QCheckBox(self.layoutWidget1)
        self.checkBox_auto_scroll.setObjectName(u"checkBox_auto_scroll")
        self.checkBox_auto_scroll.setChecked(True)

        self.horizontalLayout_2.addWidget(self.checkBox_auto_scroll)

        self.btn_clear_status = QPushButton(self.layoutWidget1)
        self.btn_clear_status.setObjectName(u"btn_clear_status")

        self.horizontalLayout_2.addWidget(self.btn_clear_status)

        self.btn_save_log = QPushButton(self.layoutWidget1)
        self.btn_save_log.setObjectName(u"btn_save_log")

        self.horizontalLayout_2.addWidget(self.btn_save_log)


        self.gridLayout.addWidget(self.Status, 1, 0, 1, 4)

        self.Display = QFrame(self.centralwidget)
        self.Display.setObjectName(u"Display")
        self.Display.setStyleSheet(u"QFrame{\n"
"	background-color:rgb(245, 245, 245)\n"
"}")
        self.Display.setFrameShape(QFrame.StyledPanel)
        self.Display.setFrameShadow(QFrame.Raised)
        self.stackedWidget = QStackedWidget(self.Display)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(139, -1, 1131, 931))
        self.cutter_page = QWidget()
        self.cutter_page.setObjectName(u"cutter_page")
        self.cutter_plot_display = QLabel(self.cutter_page)
        self.cutter_plot_display.setObjectName(u"cutter_plot_display")
        self.cutter_plot_display.setGeometry(QRect(20, 50, 1081, 811))
        self.cutter_plot_display.setFrameShape(QFrame.Box)
        self.cutter_plot_display.setScaledContents(True)
        self.cutter_plot_display.setAlignment(Qt.AlignCenter)
        self.label_cutterTraj = QLabel(self.cutter_page)
        self.label_cutterTraj.setObjectName(u"label_cutterTraj")
        self.label_cutterTraj.setGeometry(QRect(20, 20, 81, 16))
        self.label_cutterTraj.setFont(font1)
        self.stackedWidget.addWidget(self.cutter_page)
        self.laser_page = QWidget()
        self.laser_page.setObjectName(u"laser_page")
        self.laser_plot_widget = InteractiveMatplotlibWidget(self.laser_page)
        self.laser_plot_widget.setObjectName(u"laser_plot_widget")
        self.laser_plot_widget.setGeometry(QRect(20, 50, 1081, 811))
        self.label_laserTraj = QLabel(self.laser_page)
        self.label_laserTraj.setObjectName(u"label_laserTraj")
        self.label_laserTraj.setGeometry(QRect(20, 20, 111, 16))
        self.label_laserTraj.setFont(font1)
        self.stackedWidget.addWidget(self.laser_page)
        self.heat_page = QWidget()
        self.heat_page.setObjectName(u"heat_page")
        self.heat_animation_container = QWidget(self.heat_page)
        self.heat_animation_container.setObjectName(u"heat_animation_container")
        self.heat_animation_container.setGeometry(QRect(20, 50, 1081, 761))
        self.label_heatDist_animation = QLabel(self.heat_page)
        self.label_heatDist_animation.setObjectName(u"label_heatDist_animation")
        self.label_heatDist_animation.setGeometry(QRect(20, 20, 101, 16))
        self.label_heatDist_animation.setFont(font1)
        self.layoutWidget_2 = QWidget(self.heat_page)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(330, 830, 461, 30))
        self.horizontalLayout_3 = QHBoxLayout(self.layoutWidget_2)
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.btn_anim_play = QPushButton(self.layoutWidget_2)
        self.btn_anim_play.setObjectName(u"btn_anim_play")

        self.horizontalLayout_3.addWidget(self.btn_anim_play)

        self.btn_anim_pause = QPushButton(self.layoutWidget_2)
        self.btn_anim_pause.setObjectName(u"btn_anim_pause")

        self.horizontalLayout_3.addWidget(self.btn_anim_pause)

        self.btn_anim_reset = QPushButton(self.layoutWidget_2)
        self.btn_anim_reset.setObjectName(u"btn_anim_reset")

        self.horizontalLayout_3.addWidget(self.btn_anim_reset)

        self.btn_anim_save = QPushButton(self.layoutWidget_2)
        self.btn_anim_save.setObjectName(u"btn_anim_save")

        self.horizontalLayout_3.addWidget(self.btn_anim_save)

        self.stackedWidget.addWidget(self.heat_page)
        self.layoutWidget2 = QWidget(self.Display)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(10, 270, 131, 341))
        self.verticalLayout = QVBoxLayout(self.layoutWidget2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_cutter_change = QPushButton(self.layoutWidget2)
        self.btn_cutter_change.setObjectName(u"btn_cutter_change")
        self.btn_cutter_change.setStyleSheet(u"\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.verticalLayout.addWidget(self.btn_cutter_change)

        self.btn_laser_change = QPushButton(self.layoutWidget2)
        self.btn_laser_change.setObjectName(u"btn_laser_change")
        self.btn_laser_change.setStyleSheet(u"\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.verticalLayout.addWidget(self.btn_laser_change)

        self.btn_heat_change = QPushButton(self.layoutWidget2)
        self.btn_heat_change.setObjectName(u"btn_heat_change")
        self.btn_heat_change.setStyleSheet(u"\n"
"QPushButton::hover{\n"
"	background-color:rgb(65,184,131);\n"
"}")

        self.verticalLayout.addWidget(self.btn_heat_change)


        self.gridLayout.addWidget(self.Display, 0, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 2112, 26))
        self.file = QMenu(self.menubar)
        self.file.setObjectName(u"file")
        self.tool = QMenu(self.menubar)
        self.tool.setObjectName(u"tool")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.file.menuAction())
        self.menubar.addAction(self.tool.menuAction())
        self.file.addAction(self.actionsave)
        self.file.addAction(self.actionload)
        self.tool.addAction(self.actiontool)
        self.tool.addAction(self.actioninformation)

        self.retranslateUi(MainWindow)

        self.comboBox_trajectory_type.setCurrentIndex(0)
        self.stackedWidget_params.setCurrentIndex(0)
        self.stackedWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionsave.setText(QCoreApplication.translate("MainWindow", u"save", None))
        self.actionload.setText(QCoreApplication.translate("MainWindow", u"load", None))
        self.actiontool.setText(QCoreApplication.translate("MainWindow", u"tool", None))
        self.actioninformation.setText(QCoreApplication.translate("MainWindow", u"info", None))
        self.label_hand.setText(QCoreApplication.translate("MainWindow", u"\u624b\u52a8\u8f93\u5165", None))
        self.label_Gcode.setText(QCoreApplication.translate("MainWindow", u"G\u4ee3\u7801\u8f93\u5165", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u94e3\u524a\u53c2\u6570", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u5149\u53c2\u6570", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u6750\u6599\u53c2\u6570", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u70ed\u5bfc\u7387", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u6bd4\u70ed\u5bb9", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u6750\u6599\u5bc6\u5ea6", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u5149\u529f\u7387", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u5149\u534a\u5f84", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"\u94e3\u5200\u76f4\u5f84", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"\u4e3b\u8f74\u8f6c\u901f", None))
        self.comboBox_trajectory_type.setItemText(0, QCoreApplication.translate("MainWindow", u"line", None))
        self.comboBox_trajectory_type.setItemText(1, QCoreApplication.translate("MainWindow", u"sin", None))
        self.comboBox_trajectory_type.setItemText(2, QCoreApplication.translate("MainWindow", u"zigzag", None))

        self.lineEdit_sinFrequency.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Hz", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"\u8f68\u8ff9\u632f\u5e45", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"\u8f68\u8ff9\u9891\u7387", None))
        self.lineEdit_sinAmplitude.setPlaceholderText(QCoreApplication.translate("MainWindow", u"m", None))
        self.lineEdit_num_zigzags.setText("")
        self.lineEdit_num_zigzags.setPlaceholderText("")
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"\u952f\u9f7f\u6ce2\u6570\u91cf", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"\u952f\u9f7f\u6ce2\u632f\u5e45", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"\u952f\u9f7f\u6ce2\u504f\u7f6e", None))
        self.lineEdit_amplitude_zigzag.setText("")
        self.lineEdit_amplitude_zigzag.setPlaceholderText(QCoreApplication.translate("MainWindow", u"m", None))
        self.lineEdit_offset.setText("")
        self.lineEdit_offset.setPlaceholderText(QCoreApplication.translate("MainWindow", u"m", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"\u952f\u9f7f\u6ce2\u5468\u671f", None))
        self.lineEdit_period.setText("")
        self.lineEdit_period.setPlaceholderText(QCoreApplication.translate("MainWindow", u"s", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"\u8f68\u8ff9\u7c7b\u578b", None))
        self.lineEdit_Det.setPlaceholderText(QCoreApplication.translate("MainWindow", u"m", None))
        self.lineEdit_nC.setPlaceholderText(QCoreApplication.translate("MainWindow", u"r/min", None))
        self.lineEdit_k.setPlaceholderText(QCoreApplication.translate("MainWindow", u"W/(m\u00b7K)", None))
        self.lineEdit_cp.setPlaceholderText(QCoreApplication.translate("MainWindow", u"J/(kg\u00b7K)", None))
        self.lineEdit_rho.setPlaceholderText(QCoreApplication.translate("MainWindow", u"kg/m\u00b3", None))
        self.lineEdit_source_power.setPlaceholderText(QCoreApplication.translate("MainWindow", u"W", None))
        self.lineEdit_rb0.setPlaceholderText(QCoreApplication.translate("MainWindow", u"m", None))
#if QT_CONFIG(tooltip)
        self.btn_open_coords.setToolTip(QCoreApplication.translate("MainWindow", u"\u70b9\u51fb\u5f39\u51fa\u5750\u6807\u8f93\u5165\u8868\u683c", None))
#endif // QT_CONFIG(tooltip)
        self.btn_open_coords.setText(QCoreApplication.translate("MainWindow", u"\u8f93\u5165\u8def\u5f84\u70b9", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u8def\u5f84\u8f68\u8ff9", None))
        self.btn_cutter.setText(QCoreApplication.translate("MainWindow", u"\u68c0\u89c6\u94e3\u5200\u8f68\u8ff9", None))
        self.btn_laser.setText(QCoreApplication.translate("MainWindow", u"\u751f\u6210\u6fc0\u5149\u626b\u63cf\u8f68\u8ff9", None))
        self.btn_opt_laser.setText(QCoreApplication.translate("MainWindow", u"\u667a\u80fd\u4f18\u5316\u6fc0\u5149\u8f68\u8ff9", None))
        self.btn_heat_even.setText(QCoreApplication.translate("MainWindow", u"\u751f\u6210\u70ed\u573a\u56fe", None))
#if QT_CONFIG(tooltip)
        self.btn_upload_gcode.setToolTip(QCoreApplication.translate("MainWindow", u"\u70b9\u51fb\u5f39\u51fa\u5750\u6807\u8f93\u5165\u8868\u683c", None))
#endif // QT_CONFIG(tooltip)
        self.btn_upload_gcode.setText(QCoreApplication.translate("MainWindow", u"\u4e0a\u4f20G\u4ee3\u7801", None))
#if QT_CONFIG(tooltip)
        self.btn_set_default.setToolTip(QCoreApplication.translate("MainWindow", u"\u70b9\u51fb\u5f39\u51fa\u5750\u6807\u8f93\u5165\u8868\u683c", None))
#endif // QT_CONFIG(tooltip)
        self.btn_set_default.setText(QCoreApplication.translate("MainWindow", u"\u8bbe\u7f6e\u9ed8\u8ba4\u53c2\u6570", None))
#if QT_CONFIG(tooltip)
        self.btn_clear_params.setToolTip(QCoreApplication.translate("MainWindow", u"\u70b9\u51fb\u5f39\u51fa\u5750\u6807\u8f93\u5165\u8868\u683c", None))
#endif // QT_CONFIG(tooltip)
        self.btn_clear_params.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u7a7a\u53c2\u6570\u8f93\u5165", None))
#if QT_CONFIG(tooltip)
        self.btn_interval_exec.setToolTip(QCoreApplication.translate("MainWindow", u"\u70b9\u51fb\u5f39\u51fa\u5750\u6807\u8f93\u5165\u8868\u683c", None))
#endif // QT_CONFIG(tooltip)
        self.btn_interval_exec.setText(QCoreApplication.translate("MainWindow", u"\u6b65\u8fdb\u6267\u884c", None))
        self.textEdit_status.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Consolas','Monaco','monospace'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.checkBox_auto_scroll.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u6eda\u52a8", None))
#if QT_CONFIG(tooltip)
        self.btn_clear_status.setToolTip(QCoreApplication.translate("MainWindow", u"\u6e05\u7a7a\u6240\u6709\u72b6\u6001\u6d88\u606f", None))
#endif // QT_CONFIG(tooltip)
        self.btn_clear_status.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u9664", None))
#if QT_CONFIG(tooltip)
        self.btn_save_log.setToolTip(QCoreApplication.translate("MainWindow", u"\u5c06\u72b6\u6001\u6d88\u606f\u4fdd\u5b58\u5230\u6587\u4ef6", None))
#endif // QT_CONFIG(tooltip)
        self.btn_save_log.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u65e5\u5fd7", None))
        self.cutter_plot_display.setText("")
        self.label_cutterTraj.setText(QCoreApplication.translate("MainWindow", u"\u94e3\u5200\u8f68\u8ff9\u56fe", None))
        self.label_laserTraj.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u5149\u626b\u63cf\u8f68\u8ff9\u56fe", None))
        self.label_heatDist_animation.setText(QCoreApplication.translate("MainWindow", u"\u70ed\u573a\u53d8\u5316\u52a8\u753b", None))
        self.btn_anim_play.setText(QCoreApplication.translate("MainWindow", u"\u64ad\u653e\u52a8\u753b", None))
        self.btn_anim_pause.setText(QCoreApplication.translate("MainWindow", u"\u6682\u505c\u52a8\u753b", None))
        self.btn_anim_reset.setText(QCoreApplication.translate("MainWindow", u"\u91cd\u7f6e", None))
        self.btn_anim_save.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u52a8\u753b", None))
        self.btn_cutter_change.setText(QCoreApplication.translate("MainWindow", u"\u94e3\u5200\u8f68\u8ff9\u9875\u9762", None))
        self.btn_laser_change.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u5149\u626b\u63cf\u8f68\u8ff9\u9875\u9762", None))
        self.btn_heat_change.setText(QCoreApplication.translate("MainWindow", u"\u70ed\u573a\u52a8\u753b\u9875\u9762", None))
        self.file.setTitle(QCoreApplication.translate("MainWindow", u"\u6587\u4ef6", None))
        self.tool.setTitle(QCoreApplication.translate("MainWindow", u"\u5de5\u5177", None))
    # retranslateUi

