import sys
from PyQt5.QtWidgets import QWidget,QApplication,QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal,QObject,QDir,QTimer
from time import sleep
from Ui_TCPServer import Ui_Form
import threading
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class Heat_Qthread_function(QObject):

    signal_start_function = pyqtSignal()
    signal_update_data = pyqtSignal(object) # object 是 Python 的一个基类，表示几乎所有的类都是它的子类（或它本身）。在这里，它用作 pyqtSignal 的参数类型，意味着这个信号可以传递任何 Python 对象作为参数。
    signal_set_freq = pyqtSignal(object)
    signal_save_data = pyqtSignal(object)
    signal_openfile_save = pyqtSignal(object,object)
    
    def __init__(self,parent = None):
        super(Heat_Qthread_function,self).__init__(parent)   # 这里的线程依然还是主线程的ID
        self.buf = bytes()          
        # self.frame = bytes()
        self.frameBuf = []      # 帧数据缓冲区
        self.state = 0          # 0：未接收到帧头 1：接收到帧头 2：接收到帧尾
        self.debug = 0
        # self.offset = 7
        # self.multi = 2
        self.freq = 130         # 采样频率
        self.middleTime = 30    # 定时周期
        self.middleNum = round(self.middleTime * self.freq / 1000) + 1      # 在线帧数间隔

        self.onlineflag = True  # 当前热力图是在线还是离线
        self.onlineMiddle = 7   # 离线帧数间隔
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.timeheatMap)
        # self.timer.start(self.middleTime)        # 定时周期，ms


    def Heat_qthread_function_Init(self):
        # sleep(0.5)
        # print("HeatMap线程id:",threading.current_thread().ident)
        self.timer = QTimer()
        self.timer.timeout.connect(self.timeheatMap)
        self.timer.start(self.middleTime)        # 定时周期，ms
        # pass

    def slot_save_data(self,lst):
        self.frameBuf.extend(lst)


    def slot_openfile_save(self,lst,freq):
        # print('数据长度',len(lst))
        self.onlineflag = False
        self.onlineMiddle = round(self.middleTime * freq / 1000) + 1
        self.frameBuf = lst


    def timeheatMap(self):
        # print(len(self.frameBuf))
        if self.onlineflag:
            if len(self.frameBuf) < self.middleNum:
                return
        else:
            if len(self.frameBuf) < self.onlineMiddle:
                self.onlineflag = True      # 显示完毕              
                self.frameBuf = []
                return

        # frame = np.random.randint(low=-500, high=500, size=(10, 10))
        frame = []
        for i in range(10,0,-1):
            temp = []
            for j in range(20,10,-1):
                # print(i,j)
                temp.append(self.frameBuf[0][i - 1] + self.frameBuf[0][j - 1])
            frame.append(temp)

        # if self.debug != len(self.frameBuf):
        #     print(len(self.frameBuf))
        # self.debug = len(self.frameBuf)

        self.signal_update_data.emit(frame)
        if self.onlineflag:
            self.frameBuf[:self.middleNum] = []
        else:
            self.frameBuf[:self.onlineMiddle] = []

    def slot_set_freq(self,freq):
        self.freq = freq         # 采样频率
        # self.middleNum = round(self.middleTime * self.freq / 1000) * self.multi      # 发送热力图间隔帧数，四舍五入
        self.middleNum = round(self.middleTime * self.freq / 1000) + 1    # 发送热力图间隔帧数，四舍五入

        # print('间隔',self.middleNum)







