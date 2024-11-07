
import sys
import os
import time
import datetime
import threading

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog,QMessageBox
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal,QObject,QTimer,Qt,QPointF
from PyQt5.QtGui import QTextCursor, QColor,QIcon,QPixmap
from time import sleep
from Ui_TCPServer import Ui_Form
from TCP_Server import TCP_Server_Qthread_function
from DataHandle import Handle_Qthread_function
from FileSave import File_Qthread_function
from HeatMap import Heat_Qthread_function
from PyQt5.QtNetwork import QNetworkInterface
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis 

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import Normalize 

class InitForm(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("HD-sDMG Viewer")
        self.setWindowIcon(QIcon('./icon/panda.ico'))

        # print("主线程id:",threading.current_thread().ident)
        self.debug = 0
        self.receiveLength = 0
        self.netState = 2                   # 0:打开失败，1:开启状态，2:关闭状态
        self.holdState = True               # 1:当前显示的是开始 0:当前显示的是停止 
        # self.calibrate = [0 for _ in range(10)]        # 标定值
        self.calibrateFlag = False          # False:未标定，True:已标定
        self.lastCaliberateFlag = False
        self.heatMapRangeMax = 6000     # 热力图数据范围最大值
        self.heatMapRangeMin = -6000     # 热力图数据范围最小值
        self.sampleCount = 200
        self.lineChartRangeMax = 6000       # 曲线图范围最大值
        self.lineChartRangeMin = -1000      # 曲线图范围最小值
        self.chartData1_be = [0] * self.sampleCount     
        self.chartData1_af = [0] * self.sampleCount     
        self.chartData2_be = [0] * self.sampleCount     
        self.chartData2_af = [0] * self.sampleCount 
        self.chart1Line = 0             # chart1的通道，0~9
        self.chart2Line = 10            # chart2的通道，10~19
        self.lineName = [f'L{i}' for i in range(1,21)]
        self.heatMapText = []       # 保存热力图文本的引用
        self.heatMapData = []       # 记录热力图数据
        self.heatMapData = np.zeros((10, 10))
        self.openFileData = []      # 打开文件后转换而成的热力图数据
        self.pictures = {}          # 用以存放图片
        self.actionNum = {
            'DF':1, 'PF':1, 'E':1,
            'IN':1, 'TD':1, 'TU':1,
            'IR':1, 'ER':1, 'NP':1
        }
        self.FileSave_Init()
        self.HeatMap_Init()
        self.DataHandle_Init()
        self.TCP_Server_Init()
        self.UI_Init()

    # ------------------------------Threads------------------------------ #    
    def FileSave_Init(self):
        self.File_QThread  = QThread()           # 创建一个Qt线程
        self.File_Qthread_function = File_Qthread_function()      # 实例化对象
        self.File_Qthread_function.moveToThread(self.File_QThread)    # 将该方法移到新线程里去
        self.File_QThread.start()  
        # self.File_Qthread_function.signal_start_function.connect(self.File_Qthread_function.File_qthread_function_Init)        # 不指定触发方式，直接连接
        self.File_Qthread_function.signal_set_path.connect(self.File_Qthread_function.slot_set_path)
        self.File_Qthread_function.signal_set_isSave.connect(self.File_Qthread_function.slot_set_isSave)
        self.File_Qthread_function.signal_set_fileName.connect(self.File_Qthread_function.slot_set_fileName)
        self.File_Qthread_function.signal_open_file.connect(self.File_Qthread_function.slot_open_file)
        # self.File_Qthread_function.signal_start_function.emit()      # 触发

    def HeatMap_Init(self):
        self.Heat_QThread  = QThread()           # 创建一个Qt线程
        self.Heat_Qthread_function = Heat_Qthread_function()      # 实例化对象
        self.Heat_Qthread_function.moveToThread(self.Heat_QThread)    # 将该方法移到新线程里去
        self.Heat_QThread.start()
        self.Heat_Qthread_function.signal_start_function.connect(self.Heat_Qthread_function.Heat_qthread_function_Init)        # 不指定触发方式，直接连接
        self.Heat_Qthread_function.signal_set_freq.connect(self.Heat_Qthread_function.slot_set_freq)
        self.Heat_Qthread_function.signal_openfile_save.connect(self.Heat_Qthread_function.slot_openfile_save)
        self.Heat_Qthread_function.signal_update_data.connect(self.updatePlot)
        self.Heat_Qthread_function.signal_start_function.emit()      # 触发

    def DataHandle_Init(self):
        self.Handle_QThread  = QThread()           # 创建一个Qt线程
        self.Handle_Qthread_function = Handle_Qthread_function()      # 实例化对象
        self.Handle_Qthread_function.moveToThread(self.Handle_QThread)    # 将该方法移到新线程里去
        self.Handle_QThread.start()  
        # self.Handle_Qthread_function.signal_start_function.connect(self.Handle_Qthread_function.Handle_qthread_function_Init)        # 不指定触发方式，直接连接
        self.Handle_Qthread_function.signal_file_save_data.connect(self.File_Qthread_function.slot_save_data)       # 发送给另一个子线程
        self.Handle_Qthread_function.signal_heatMap_save_data.connect(self.Heat_Qthread_function.slot_save_data)    # 发送给另一个子线程
        self.Handle_Qthread_function.signal_caliberate_finished.connect(self.slot_caliberate_finished)
        self.Handle_Qthread_function.signal_caliberate_start.connect(self.Handle_Qthread_function.slot_caliberate_start)
        self.Handle_Qthread_function.signal_lastCaliberate.connect(self.Handle_Qthread_function.slot_lastCaliberate)
        self.Handle_Qthread_function.signal_handle_readyRead.connect(self.slot_handle_readyRead)
        self.Handle_Qthread_function.signal_showCalibrate.connect(self.slot_showCalibrate)
        self.Handle_Qthread_function.signal_recognitionResult.connect(self.recognitionResult)
        self.Handle_Qthread_function.signal_showLineChart_be.connect(self.updateChart_be)
        self.Handle_Qthread_function.signal_showLineChart_af.connect(self.updateChart_af)
        self.Handle_Qthread_function.signal_setChartFlag.connect(self.Handle_Qthread_function.slot_setChartFlag)
        self.Handle_Qthread_function.signal_setFiltFlag.connect(self.Handle_Qthread_function.slot_setFiltFlag)
        self.Handle_Qthread_function.signal_setCutoff.connect(self.Handle_Qthread_function.slot_setCutoff)
        self.Handle_Qthread_function.signal_setFs.connect(self.Handle_Qthread_function.slot_setFs)

        # self.Handle_Qthread_function.signal_start_function.emit()      # 触发

    def TCP_Server_Init(self):
        self.TCP_Server_QThread  = QThread()           # 创建一个Qt线程
        self.TCP_Server_Qthread_function = TCP_Server_Qthread_function()      # 实例化对象
        self.TCP_Server_Qthread_function.moveToThread(self.TCP_Server_QThread)    # 将该方法移到新线程里去
        self.TCP_Server_QThread.start()  
        self.TCP_Server_Qthread_function.signal_start_function.connect(self.TCP_Server_Qthread_function.TCP_Server_qthread_function_Init)        # 不指定触发方式，直接连接
        self.TCP_Server_Qthread_function.signal_closeClient.connect(self.TCP_Server_Qthread_function.slot_closeClient)        # 不指定触发方式，直接连接
        self.TCP_Server_Qthread_function.signal_sendData.connect(self.TCP_Server_Qthread_function.slot_sendData)        # 不指定触发方式，直接连接
        self.TCP_Server_Qthread_function.signal_pushButton_open.connect(self.TCP_Server_Qthread_function.slot_pushButton_open)
        self.TCP_Server_Qthread_function.signal_readyRead.connect(self.Handle_Qthread_function.slot_handle_data)        # 发送给另一个子线程
        self.TCP_Server_Qthread_function.signal_pushButton_open_flag.connect(self.slot_pushButton_open_flag)
        self.TCP_Server_Qthread_function.signal_newClient.connect(self.slot_newClient)
        self.TCP_Server_Qthread_function.signal_start_function.emit()      # 触发

    # ------------------------------UI------------------------------ #
    def UI_Init(self):
        self.ui.lineEdit_port.setText('8088')       # 写一个默认端口值
        self.ui.comboBox_ip.addItems(self.search_ip())
        self.ui.pushButton_open.clicked.connect(self.pushButton_open)
        self.ui.pushButton_cleanReceive.clicked.connect(self.pushButton_cleanReceive)
        self.ui.pushButton_disconnect.clicked.connect(self.pushButton_clientDisconnect)
        # self.ui.checkBox_motion.stateChanged.connect(self.checkBox_motion)
        self.ui.checkBox_motion.setEnabled(False)

        # 文件控件
        self.ui.lineEdit_fileNum.setText('1')
        self.ui.comboBox_fileName.addItems({'DF','PF','E','IN','TD','TU','IR','ER','NP'})
        self.ui.comboBox_fileName.setCurrentText('NP')
        # self.ui.comboBox_fileName.setEditable(True)  # 使能下拉框输入
        self.ui.comboBox_fileName.currentTextChanged.connect(self.comboBox_fileName)
        self.ui.checkBox_fileSave.stateChanged.connect(self.checkBox_fileSave)
        self.ui.comboBox_fileName.setEnabled(False)
        self.ui.lineEdit_fileNum.setEnabled(False)
        self.ui.checkBox_fileSave.setEnabled(False)
        
        # 文件打开控件
        self.ui.pushButton_openFile.clicked.connect(self.pushButton_openFile)
        self.ui.pushButton_openFileStart.clicked.connect(self.pushButton_openFileStart)
        self.ui.pushButton_openFileStart.setEnabled(False)

        # 指令控件
        self.ui.pushButton_hold.clicked.connect(self.pushButton_hold)
        self.ui.comboBox_freq.addItems({'130','100'})
        self.ui.comboBox_freq.setEditable(True)  # 使能下拉框输入
        self.ui.pushButton_setFreq.clicked.connect(self.pushButton_setFreq)
        self.ui.pushButton_calibrate.clicked.connect(self.pushButton_calibrate)
        self.ui.pushButton_calibrate.setEnabled(False)
        self.ui.pushButton_lastCalibrate.clicked.connect(self.pushButton_lastCalibrate)
        self.ui.pushButton_lastCalibrate.setEnabled(False)    
        self.ui.pushButton_hold.setEnabled(False)
        # self.ui.comboBox_freq.setEnabled(False)
        self.ui.pushButton_setFreq.setEnabled(False)

        # 曲线图相关
        self.ui.comboBox_Line1.addItems({'L1','L2','L3','L4','L5','L6','L7','L8','L9','L10'})
        self.ui.comboBox_Line1.setCurrentText(self.lineName[self.chart1Line])
        self.ui.comboBox_Line1.currentTextChanged.connect(self.comboBox_Line1)
        self.ui.comboBox_Line2.addItems({'L11','L12','L13','L14','L15','L16','L17','L18','L19','L20'})
        self.ui.comboBox_Line2.setCurrentText(self.lineName[self.chart2Line])
        self.ui.comboBox_Line2.currentTextChanged.connect(self.comboBox_Line2)
        self.ui.checkBox_LineChart.stateChanged.connect(self.checkBox_LineChart)
        self.ui.lineEdit_Freq.setText('6')
        self.ui.lineEdit_Freq.setEnabled(False)
        self.ui.checkBox_Filter.stateChanged.connect(self.checkBox_Filter)
        self.ui.checkBox_Filter.setChecked(True)

        self.series1_be = QLineSeries() 
        self.series1_af = QLineSeries() 
        self.series2_be = QLineSeries() 
        self.series2_af = QLineSeries() 

        self.chart1 = QChart() 
        self.chart1.addSeries(self.series1_be)   # Add the series to the chart
        self.chart1.addSeries(self.series1_af)   # Add the series to the chart
        self.chart1.setTitle(self.lineName[self.chart1Line])
        self.chart2 = QChart() 
        self.chart2.addSeries(self.series2_be)   # Add the series to the chart
        self.chart2.addSeries(self.series2_af)   # Add the series to the chart
        self.chart2.setTitle(self.lineName[self.chart2Line])

        axisX1 = QValueAxis() 
        axisX1.setRange(0, self.sampleCount) 
        axisX1.setLabelFormat('%g')          # 设置X轴的标签格式
        axisY1 = QValueAxis() 
        axisY1.setRange(self.lineChartRangeMin, self.lineChartRangeMax)         
        axisX2 = QValueAxis() 
        axisX2.setRange(0, self.sampleCount) 
        axisX2.setLabelFormat('%g')          # 设置X轴的标签格式
        axisY2 = QValueAxis() 
        axisY2.setRange(self.lineChartRangeMin, self.lineChartRangeMax) 

        self.chart1.addAxis(axisX1, Qt.AlignBottom)   # Add X-axis to the chart
        self.series1_be.attachAxis(axisX1)               # 将系列连接到 X 轴
        self.series1_af.attachAxis(axisX1)               # 将系列连接到 X 轴
        self.chart1.addAxis(axisY1, Qt.AlignLeft)     # Add Y-axis to the chart
        self.series1_be.attachAxis(axisY1)               # 将系列连接到 Y 轴
        self.series1_af.attachAxis(axisY1)               # 将系列连接到 Y 轴
        self.chart1.legend().hide()                  # 隐藏图表图例 
        self.chart2.addAxis(axisX2, Qt.AlignBottom)   # Add X-axis to the chart
        self.series2_be.attachAxis(axisX2)               # 将系列连接到 X 轴
        self.series2_af.attachAxis(axisX2)               # 将系列连接到 X 轴
        self.chart2.addAxis(axisY2, Qt.AlignLeft)     # Add Y-axis to the chart
        self.series2_be.attachAxis(axisY2)               # 将系列连接到 Y 轴
        self.series2_af.attachAxis(axisY2)               # 将系列连接到 Y 轴
        self.chart2.legend().hide()                  # 隐藏图表图例

        chartView1 = QChartView(self.chart1)  # Create a view for the chart
        chartView1.setMinimumSize(300, 200)
        chartView2 = QChartView(self.chart2)  # Create a view for the chart
        chartView2.setMinimumSize(300, 200)
        self.ui.verticalLayout_LineChart.addWidget(chartView1)
        self.ui.verticalLayout_LineChart.addWidget(chartView2)

        # 热力图相关
        self.ui.checkBox_heatShowNum.stateChanged.connect(self.checkBox_heatShowNum)
        self.ui.checkBox_ShowHeatMap.stateChanged.connect(self.checkBox_ShowHeatMap)
        self.ui.checkBox_ShowHeatMap.setChecked(True)
        self.ui.pushButton_HeatSave.clicked.connect(self.pushButton_HeatSave)
        # 从matplotlib的颜色映射库中获取了名为'Blues'的默认颜色映射，并将其存储在变量cmap中。'Blues'是一个从蓝色渐变到白色的颜色映射。
        # cmap = plt.cm.get_cmap('Blues')
        # np.linspace(0.3, 0.8, cmap.N)生成了一个从0.3到0.8的等差数列，其长度（cmap.N）与原始颜色映射中的颜色数量相同。然后，cmap(np.linspace(0.3, 0.8, cmap.N))将这个等差数列应用到'Blues'颜色映射上，以获取一个从颜色映射中某个中间点（大约30%的位置）到某个稍深位置（大约80%的位置）的颜色序列
        # colors = cmap(np.linspace(0.3, 0.8, cmap.N))

        # FF0000 红色，00FF00 绿色，0000FF 蓝色，FFFF00 纯黄色，FFCC00 稍暗黄色，
        white = -self.heatMapRangeMin / (self.heatMapRangeMax - self.heatMapRangeMin)
        colors = [  (0,     '#0000FF'),  # 蓝色
                    (white, '#FFFFFF'),  # 白色
                    (1,     '#FFDD00')]  # 黄色

        # 从给定的颜色列表（colors）中创建一个新的颜色映射
        # self.custom_colormap = plt.cm.get_cmap('coolwarm', 5)  # 从'coolwarm'中选择5个颜色
        self.custom_colormap = mcolors.LinearSegmentedColormap.from_list('Chopped_Color', colors)

        # 使用matplotlib.pyplot的subplots函数创建一个新的图形（figure）和一个子图（axes或简称为ax）。
        # self.figure保存了这个图形的引用，你可以在后续的代码中修改或更新这个图形。
        # self.ax保存了子图的引用，你可以在这个子图上绘制各种图表元素（如线条、点、标签等）。
        self.figure, self.ax = plt.subplots()

        # 创建一个FigureCanvas对象，它通常是matplotlib后端与GUI框架（如Qt）之间的桥梁。
        # 这个FigureCanvas对象允许你在GUI中嵌入matplotlib的图形。
        # 你将之前创建的self.figure作为参数传递给FigureCanvas的构造函数，这样FigureCanvas就知道它应该显示哪个图形了。        
        self.canvas = FigureCanvas(self.figure)
        
        # 这行代码假设你有一个名为layout的布局对象（可能是QGridLayout、QHBoxLayout、QVBoxLayout等，取决于你使用的Qt框架）。
        # 你使用addWidget方法将self.canvas（即嵌入matplotlib图形的FigureCanvas）添加到这个布局中。
        # 这意味着当GUI窗口显示时，self.canvas（即matplotlib图形）将作为GUI的一部分显示
        self.ui.verticalLayout_HeatMap.addWidget(self.canvas)

        self.myNorm = Normalize(vmin=self.heatMapRangeMin, vmax=self.heatMapRangeMax)  

        # 使用self.ax.imshow()方法在一个已经存在的子图（self.ax）上绘制一个图像。
        # 绘制的图像是一个全零的二维数组，其形状与self.data的前两个维度相同（self.data.shape[0]是行数，self.data.shape[1]是列数）。这意味着热图的初始状态是一个空白的热图，没有任何数据点。
        # cmap=custom_colormap指定了用于绘制热图的颜色映射（colormap）。这里假设custom_colormap是一个之前定义好的颜色映射。
        # self.initial_heatmap保存了这次绘制的结果（一个matplotlib.image.AxesImage对象），以便后续可以更新这个热图。         
        self.initial_heatmap = self.ax.imshow(np.zeros((10, 10)), cmap=self.custom_colormap, norm = self.myNorm)
        # 使用self.figure.colorbar()方法在图形（self.figure）上添加一个颜色条（colorbar）。
        # 这个颜色条对应于之前通过self.ax.imshow()绘制的热图（即self.initial_heatmap）。
        # ax=self.ax指定了颜色条应该与哪个子图（axes）相关联。在这里，它与self.ax相关联。
        # orientation='vertical'指定了颜色条的方向是垂直的。如果不指定，默认也是垂直的。
        # self.colorbar保存了这个颜色条的引用，以便后续可以对其进行修改或更新。        
        self.colorbar = self.figure.colorbar(self.initial_heatmap, ax=self.ax, orientation='vertical')
        self.ax.set_xticks([i for i in range(10)])  # 设置x轴刻度位置  
        self.ax.set_yticks([i for i in range(10)])  # 设置y轴刻度位置   
        self.ax.set_xticklabels([i for i in range(20,10,-1)])  # 设置x轴刻度标签  
        self.ax.set_yticklabels([i for i in range(10,0,-1)])  # 设置y轴刻度标签  
        for i in range(0,10):
            temp = []
            for j in range(0,10):
                text = self.ax.text(j, i, '', ha='center', va='center', color='black',fontsize=8) 
                temp.append(text)
            self.heatMapText.append(temp)

        # 加载图片
        breadth = 490
        self.pictures['NP'] = QPixmap("./pictures/中立位.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['DF'] = QPixmap("./pictures/背屈.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['PF'] = QPixmap("./pictures/跖屈.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['E']  = QPixmap("./pictures/外翻.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['IN'] = QPixmap("./pictures/内翻.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['TD'] = QPixmap("./pictures/扣脚趾.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['TU'] = QPixmap("./pictures/跷脚指.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['IR'] = QPixmap("./pictures/外旋.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.pictures['ER'] = QPixmap("./pictures/内旋.png").scaled(breadth,breadth*2,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.ui.label_Picture.setPixmap(self.pictures[self.ui.comboBox_fileName.currentText()])

    def comboBox_Line1(self,line):
        # print('选中',self.lineName.index(line))
        self.chart1Line = self.lineName.index(line)
        self.chart1.setTitle(self.lineName[self.chart1Line])        
        self.chartData1_be = [0] * self.sampleCount     
        self.series1_be.clear()
        self.chartData1_af = [0] * self.sampleCount     
        self.series1_af.clear()

    def comboBox_Line2(self,line):
        # print('选中',self.lineName.index(line))
        self.chart2Line = self.lineName.index(line)
        self.chart2.setTitle(self.lineName[self.chart2Line])        
        self.chartData2_be = [0] * self.sampleCount     
        self.series2_be.clear()
        self.chartData2_af = [0] * self.sampleCount
        self.series2_af.clear()
        
    def checkBox_LineChart(self,state):
        if state == 2:
            self.Handle_Qthread_function.signal_setChartFlag.emit(True)
        else:
            self.Handle_Qthread_function.signal_setChartFlag.emit(False)
            self.chartData1_be = [0] * self.sampleCount     
            self.chartData2_be = [0] * self.sampleCount     
            self.series1_be.clear()
            self.series2_be.clear()
            self.chartData1_af = [0] * self.sampleCount     
            self.chartData2_af = [0] * self.sampleCount
            self.series1_af.clear()
            self.series2_af.clear()

    def checkBox_Filter(self,state):
        if state == 2:
            self.ui.lineEdit_Freq.setEnabled(False)
            self.Handle_Qthread_function.signal_setCutoff.emit(int(self.ui.lineEdit_Freq.text()))
            self.Handle_Qthread_function.signal_setFiltFlag.emit(True)
        else:
            self.ui.lineEdit_Freq.setEnabled(True)
            self.Handle_Qthread_function.signal_setFiltFlag.emit(False)
            self.chartData1_af = [0] * self.sampleCount     
            self.chartData2_af = [0] * self.sampleCount
            self.series1_af.clear()
            self.series2_af.clear()


    def updateChart_be(self,data,windowLen):
        # print('更新原始数据',len(data),windowLen)
        self.chartData1_be[:windowLen] = []
        self.chartData1_be.extend([row[self.chart1Line] for row in data])
        self.series1_be.clear()
        for i, value in enumerate(self.chartData1_be):
            self.series1_be.append(QPointF(i, value))   # 向系列添加新数据点
        self.chartData2_be[:windowLen] = []
        self.chartData2_be.extend([row[self.chart2Line] for row in data])        
        self.series2_be.clear()
        for i, value in enumerate(self.chartData2_be):
            self.series2_be.append(QPointF(i, value))   # 向系列添加新数据点

    def updateChart_af(self,data,windowLen):
        # print('更新滤波数据',len(data),windowLen)
        self.chartData1_af[:windowLen] = []
        self.chartData1_af.extend([row[self.chart1Line] for row in data])
        self.series1_af.clear()
        for i, value in enumerate(self.chartData1_af):
            self.series1_af.append(QPointF(i, value))   # 向系列添加新数据点
        self.chartData2_af[:windowLen] = []
        self.chartData2_af.extend([row[self.chart2Line] for row in data])
        self.series2_af.clear()
        for i, value in enumerate(self.chartData2_af):
            self.series2_af.append(QPointF(i, value))   # 向系列添加新数据点


    def recognitionResult(self,result):
        self.ui.label_Picture.setPixmap(self.pictures[result])
        # print('识别结果',result)


    def checkBox_motion(self,state):
        if state == 2:
            # print('选中保存')
            self.File_Qthread_function.signal_set_path.emit('./recognition/')        # 设置路径
            now = datetime.datetime.now()
            date_time_tag = now.strftime("%Y%m%d_%H%M%S")        
            self.File_Qthread_function.signal_set_fileName.emit(f'Recognition-{date_time_tag}')
            self.File_Qthread_function.signal_set_isSave.emit(True)                    # 设置标志位
            # fileName = self.ui.comboBox_fileName.currentText() + '-' + self.ui.lineEdit_fileNum.text()                  
            # self.File_Qthread_function.signal_set_fileName.emit(fileName)           # 设置文件名
            self.File_Qthread_function.signal_open_file.emit(True)                      # 打开文件要后打开
            self.ui.checkBox_fileSave.setEnabled(False)
            self.Handle_Qthread_function.signal_setEngineFlag.emit(True)
        else:
            self.File_Qthread_function.signal_set_isSave.emit(False)
            self.ui.checkBox_fileSave.setEnabled(True)
            self.Handle_Qthread_function.signal_setEngineFlag.emit(False)



    def pushButton_openFileStart(self):
        data = self.openFileData.copy()     # 直接赋值是传递的引用，要复制，用copy
        freq = int(self.ui.comboBox_freq.currentText())
        self.Heat_Qthread_function.signal_openfile_save.emit(data,freq)

        # if self.ui.checkBox_motion.isChecked():
        # recog = self.openFileData.copy()     # 直接赋值是传递的引用，要复制，用copy


    def pushButton_openFile(self):
        self.ui.pushButton_openFileStart.setEnabled(False)
        self.ui.label_openFileName.setText('正在打开...')
        filePath, _ = QFileDialog.getOpenFileName(self,'打开文件',os.getcwd(),'CSV Files (*.csv)')
        if not filePath:
            self.ui.label_openFileName.setText('文件名：')
            QMessageBox.warning(self,'错误信息','未选择文件！')
            # print('filename is empty')
        else:
            name = filePath[filePath.rfind('/') + 1:]       # 得到文件名
            self.ui.label_openFileName.setText('文件名：' + name)

            # 读取CSV文件
            df = pd.read_csv(filePath)  
            self.openFileData = df.values.tolist()

            if self.netState == 2:
                self.ui.pushButton_openFileStart.setEnabled(True)


    def slot_caliberate_finished(self):
        self.ui.pushButton_calibrate.setEnabled(False) 
        self.ui.pushButton_lastCalibrate.setEnabled(False)
        self.ui.comboBox_fileName.setEnabled(True)
        self.ui.lineEdit_fileNum.setEnabled(True)
        self.ui.checkBox_fileSave.setEnabled(True)
        self.ui.checkBox_motion.setEnabled(True)
        self.ui.pushButton_hold.setEnabled(True)
        # self.ui.comboBox_freq.setEnabled(True)
        self.ui.pushButton_setFreq.setEnabled(True)
        self.calibrateFlag = True
        if self.lastCaliberateFlag == False:
            self.send_data('hold')

    def pushButton_calibrate(self):
        self.Handle_Qthread_function.signal_caliberate_start.emit()
        self.send_data('hold')
        self.ui.pushButton_lastCalibrate.setEnabled(False)
        
    def pushButton_lastCalibrate(self):
        self.Handle_Qthread_function.signal_lastCaliberate.emit()
        self.lastCaliberateFlag = True
        self.ui.pushButton_calibrate.setEnabled(False)

    def checkBox_ShowHeatMap(self,state):
        if state == 0:
            self.pushButton_cleanReceive()

    def pushButton_HeatSave(self):
        # if len(self.heatMapData) == 0:
        #     return

        now = datetime.datetime.now()
        date_time_tag = now.strftime("%Y%m%d_%H%M%S")        
        base_filename = self.ui.comboBox_fileName.currentText() + '-' + str(self.ui.lineEdit_fileNum.text())
        filename = f"{base_filename}-{date_time_tag}.jpeg"

        fig, ax = plt.subplots()
        heatmap = ax.imshow(self.heatMapData, cmap=self.custom_colormap, norm = self.myNorm)
        ax.set_xticks([i for i in range(10)])  # 设置x轴刻度位置  
        ax.set_yticks([i for i in range(10)])  # 设置y轴刻度位置   
        ax.set_xticklabels([i for i in range(20,10,-1)])  # 设置x轴刻度标签  
        ax.set_yticklabels([i for i in range(10,0,-1)])  # 设置y轴刻度标签          
        if self.ui.checkBox_heatShowNum.isChecked():
            for i in range(0,10):
                for j in range(0,10):
                    # ax.text(j, i,str(self.heatMapData), ha='center', va='center', color='black',fontsize=8) 
                    ax.text(j, i,str(self.heatMapData[i][j]), ha='center', va='center', color='black',fontsize=8) 
        plt.colorbar(heatmap, ax=ax, orientation='vertical')
        # plt.savefig(filename, dpi=500, format='jpeg')
        plt.savefig(filename, dpi=500, format='png')
        plt.close(fig)


    def checkBox_heatShowNum(self,state):
        if state == 0:      # 如果取消了勾选
            # print('取消勾选')
            for i in range(0,10):
                for j in range(0,10):
                    self.heatMapText[i][j].set_text('')
                        # self.heatMapText[i][j].set_fontsize(6)
            self.canvas.draw_idle()
        elif state == 2: # 如果勾选了，将上次的数据显示出来
            for i in range(0,10):
                for j in range(0,10):
                    self.heatMapText[i][j].set_text(str(self.heatMapData[i][j]))
                        # self.heatMapText[i][j].set_fontsize(6)
            self.canvas.draw_idle()


    def updatePlot(self,data):
        self.heatMapData = data     # 记录数据
        if self.ui.checkBox_ShowHeatMap.isChecked():
            # 将新的数据（layer_sum）设置为self.initial_heatmap这个热图的数据，从而更新图形窗口中显示的热图。
            self.initial_heatmap.set_data(data)
            # 这行代码设置了颜色映射（colormap）的范围。set_clim方法允许你指定颜色映射的最小值（vmin）和最大值（vmax）。
            # 这里，我们使用np.min(layer_sum)和np.max(layer_sum)来自动计算layer_sum数组中的最小值和最大值，
            # 并将它们设置为颜色映射的范围。这样做可以确保热图的颜色映射会根据新的数据范围进行调整。        
            self.initial_heatmap.set_clim(vmin=self.heatMapRangeMin, vmax=self.heatMapRangeMax)
            if self.ui.checkBox_heatShowNum.isChecked():
                for i in range(0,10):
                    for j in range(0,10):
                        self.heatMapText[i][j].set_text(str(data[i][j]))
                        # self.heatMapText[i][j].set_fontsize(6)
            # 重新绘制图形窗口的画布
            self.canvas.draw_idle()


    def pushButton_hold(self):
        if self.netState == 1:              # 网络处于打开状态
            if self.holdState == False:      # 表示要将停止改为开始，也即点击停止
                if self.ui.checkBox_fileSave.isChecked():
                    fileName = self.ui.comboBox_fileName.currentText()
                    self.actionNum[fileName] = self.actionNum[fileName] + 1
                    self.ui.lineEdit_fileNum.setText(str(self.actionNum[fileName]))
                self.ui.pushButton_hold.setText('开始')
                self.ui.pushButton_hold.setStyleSheet('color:black')
                if self.calibrateFlag == True:
                    self.ui.comboBox_fileName.setEnabled(True)
                    self.ui.lineEdit_fileNum.setEnabled(True)
                    self.ui.checkBox_fileSave.setEnabled(True)
                    self.ui.checkBox_motion.setEnabled(True)
                    # self.ui.comboBox_freq.setEnabled(True)
                    self.ui.pushButton_setFreq.setEnabled(True)   
                self.holdState = True 
                self.send_data('hold')
            elif self.holdState == True:   # 表示要将开始改为停止，也即点击开始
                if self.ui.checkBox_fileSave.isChecked():
                    # self.File_Qthread_function.signal_open_file.emit(False)                      # 关闭文件要先关闭
                    fileName = self.ui.comboBox_fileName.currentText()
                    fileNum = self.ui.lineEdit_fileNum.text()
                    if self.actionNum[fileName] != int(fileNum):
                        self.actionNum[fileName] = int(fileNum)
                    temp = fileName + '-' + fileNum
                    self.File_Qthread_function.signal_set_fileName.emit(temp)
                    self.File_Qthread_function.signal_open_file.emit(True)                      # 打开文件要后打开
                self.ui.pushButton_hold.setText('停止')
                self.ui.pushButton_hold.setStyleSheet('color:red')
                self.ui.comboBox_fileName.setEnabled(False)
                self.ui.lineEdit_fileNum.setEnabled(False)
                self.ui.checkBox_fileSave.setEnabled(False)
                self.ui.checkBox_motion.setEnabled(False)
                # self.ui.comboBox_freq.setEnabled(False)
                self.ui.pushButton_setFreq.setEnabled(False)
                self.holdState = False
                self.send_data('hold')
        elif self.netState == 2:              # 网络处于关闭状态
            if self.calibrateFlag == True:
                self.ui.comboBox_fileName.setEnabled(True)
                self.ui.lineEdit_fileNum.setEnabled(True)
                self.ui.checkBox_fileSave.setEnabled(True)            
                self.ui.checkBox_motion.setEnabled(True)
            self.ui.pushButton_hold.setText('开始')
            self.ui.pushButton_hold.setStyleSheet('color:black')            
            self.ui.pushButton_hold.setEnabled(False)
            # self.ui.comboBox_freq.setEnabled(False)
            self.ui.pushButton_setFreq.setEnabled(False)
            self.holdState = True
            self.receiveLength = 0      # 重新打开时，帧数改为0，重新接收
            self.ui.label_receiveNum.setText('接收:0') # 显示接帧数

    def pushButton_setFreq(self):
        freq = self.ui.comboBox_freq.currentText()
        freq_str = 'freq=' + freq
        self.send_data(freq_str)
        self.Handle_Qthread_function.signal_setFs.emit(int(freq))
        self.Heat_Qthread_function.signal_set_freq.emit(int(freq))

    def comboBox_fileName(self,fileName):
        # print(str)
        # self.File_Qthread_function.signal_open_file.emit(False)                      # 关闭文件要先关闭
        # str = str + '-' + self.ui.lineEdit_fileNum.text()
        # self.File_Qthread_function.signal_set_fileName.emit(str)
        # self.File_Qthread_function.signal_open_file.emit(True)                      # 打开文件要后打开
        self.ui.lineEdit_fileNum.setText(str(self.actionNum[fileName]))
        if not self.ui.checkBox_motion.isChecked():
            self.ui.label_Picture.setPixmap(self.pictures[fileName])
            # print(fileName)
    

    # 搜索本机ip，ipv4版本
    def search_ip(self):
        list_ip = QNetworkInterface.allAddresses()      # 拿到所有ip
        scan_ip = []
        for ip in list_ip:
            # print(ip.toString())
            if ip.isNull():
                continue
            nprotocol = ip.protocol()
            if nprotocol == 0:      # 等于0时拿到的是Ipv4
                # print(ip.toString())
                scan_ip.append(ip.toString())
        return scan_ip


    # 槽函数：点击打开按钮
    def pushButton_open(self):
        parameter = {}
        parameter['ip'] = self.ui.comboBox_ip.currentText()
        parameter['port'] = self.ui.lineEdit_port.text()
        self.TCP_Server_Qthread_function.signal_pushButton_open.emit(parameter)        # 发送给子进程   


    def send_data(self,data):
        send_buff = data + '\r\n'               # 拿到当前值 + '\r\n'      
        Byte_data = str.encode(send_buff)       # 将字符串编码（或转换）为字节序列（bytes）

        parameter = {}
        parameter['ip_port'] = self.ui.comboBox_clientIp.currentText()
        parameter['data'] = Byte_data

        self.TCP_Server_Qthread_function.signal_sendData.emit(parameter)        # 发送给子进程


    def pushButton_cleanReceive(self):
        self.ui.textEdit_receive.clear()
        temp = np.zeros((10, 10))
        # temp = self.ax.imshow(np.zeros((10, 10)), cmap=self.custom_colormap)
        self.updatePlot(temp)


    def pushButton_clientDisconnect(self):
        # print('断开客户端')
        ip_port = self.ui.comboBox_clientIp.currentText()
        self.TCP_Server_Qthread_function.signal_closeClient.emit(ip_port)


    def checkBox_fileSave(self,state):
        if state == 2:
            # print('选中保存')
            folder_selected = QFileDialog.getExistingDirectory(self, "选择一个文件夹")
            if folder_selected:
                self.File_Qthread_function.signal_set_path.emit(folder_selected)        # 设置路径
                self.File_Qthread_function.signal_set_isSave.emit(True)                    # 设置标志位
                # fileName = self.ui.comboBox_fileName.currentText() + '-' + self.ui.lineEdit_fileNum.text()               
                # self.File_Qthread_function.signal_set_fileName.emit(fileName)           # 设置文件名
                # self.File_Qthread_function.signal_open_file.emit(True)                      # 打开文件要后打开
                self.ui.checkBox_motion.setEnabled(False)

            else:
                QMessageBox.warning(self,'错误信息','请选择有效的保存路径！')
                self.File_Qthread_function.signal_set_path.emit('')
                self.File_Qthread_function.signal_set_isSave.emit(False)                
                self.ui.checkBox_motion.setEnabled(True)
        else:
            self.File_Qthread_function.signal_set_isSave.emit(False)          
            self.ui.checkBox_motion.setEnabled(True)


    def slot_pushButton_open_flag(self, state):
        # print("打开状态",state)
        self.netState = state
        if state == 0:
            # print("打开失败")
            QMessageBox.warning(self,'警告','打开失败，检测该端口是否被占用')
        elif state == 1:
            # print("打开成功")
            self.ui.pushButton_open.setText('关闭')
            self.ui.pushButton_open.setStyleSheet('color:red')
            self.ui.comboBox_ip.setEnabled(False)
            self.ui.lineEdit_port.setEnabled(False)
            # self.receiveLength = 0      # 重新打开时，帧数改为0，重新接收
            # self.ui.label_receiveNum.setText('接收:0') # 显示接帧数
            if self.calibrateFlag == True:
                self.ui.pushButton_hold.setEnabled(True)
                # self.ui.comboBox_freq.setEnabled(True)
                self.ui.pushButton_setFreq.setEnabled(True)
            self.ui.pushButton_openFileStart.setEnabled(False)
        else:
            # print("已关闭")
            self.ui.pushButton_open.setText('打开')
            self.ui.pushButton_open.setStyleSheet('color:black')
            self.ui.comboBox_ip.setEnabled(True)
            self.ui.lineEdit_port.setEnabled(True)
            # self.holdState = False
            self.pushButton_hold()      # 成功关闭后，停止接收数据
            # self.ui.pushButton_hold.setEnabled(False)
            # self.ui.comboBox_freq.setEnabled(False)
            # self.ui.pushButton_setFreq.setEnabled(False)
            # self.ui.pushButton_openFileStart.setEnabled(True)

    def slot_showCalibrate(self,CaStr):
        self.ui.textEdit_receive.clear()
        # 时间戳，颜色变化
        self.ui.textEdit_receive.insertPlainText('\n标定值：\n\n' + CaStr)
        if self.ui.checkBox_time.checkState():      # 如果勾选了时间戳
            time_str = '\n' + time.strftime("%Y-%m-%d %H:%M:%S" , time.localtime()) + ' '
            self.ui.textEdit_receive.insertPlainText(time_str)  # 与 append 方法不同，insertPlainText 不会在文本末尾添加新行，而是将文本插入到当前光标位置。
        self.ui.textEdit_receive.moveCursor(QTextCursor.End)        # 告诉 QTextCursor 对象将其位置移动到当前文本内容的末尾。

    # 更新显示
    def slot_handle_readyRead(self,length,frame_string):
        # 收到了第一帧数据
        if self.receiveLength == 0: 
            if self.calibrateFlag == False:  
                self.ui.pushButton_calibrate.setEnabled(True)   # 可以开始标定
                self.ui.pushButton_lastCalibrate.setEnabled(True)
            self.holdState = False
            self.pushButton_hold()      # 改为开始状态

        self.receiveLength = self.receiveLength + length
        self.ui.label_receiveNum.setText("接收:" + str(self.receiveLength) + '帧') # 显示接帧数

        self.ui.textEdit_receive.clear()
        # 时间戳，颜色变化
        self.ui.textEdit_receive.insertPlainText(frame_string)
        if self.ui.checkBox_time.checkState():      # 如果勾选了时间戳
            time_str = '\n' + time.strftime("%Y-%m-%d %H:%M:%S" , time.localtime()) + ' '
            self.ui.textEdit_receive.insertPlainText(time_str)  # 与 append 方法不同，insertPlainText 不会在文本末尾添加新行，而是将文本插入到当前光标位置。
        self.ui.textEdit_receive.moveCursor(QTextCursor.End)        # 告诉 QTextCursor 对象将其位置移动到当前文本内容的末尾。


    def slot_newClient(self,parameter):
        self.ui.comboBox_clientIp.clear()
        self.ui.comboBox_clientIp.addItems(parameter)
        # print(parameter)


    # ------------------------------close------------------------------ #
    def closeEvent(self, event):
        # 结束线程
        self.TCP_Server_QThread.quit()
        self.TCP_Server_QThread.wait()
        del self.TCP_Server_Qthread_function

        self.File_QThread.quit()
        self.File_QThread.wait()
        del self.File_Qthread_function

        self.Handle_QThread.quit()
        self.Handle_QThread.wait()
        del self.Handle_Qthread_function
  
        self.Heat_QThread.quit()
        self.Heat_QThread.wait()
        del self.Heat_Qthread_function


if __name__ == '__main__':
    
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    w1 = InitForm()

    # 展示窗口
    w1.show()

    # 程序进行循环等待状态
    # app.exec()
    sys.exit(app.exec_())


