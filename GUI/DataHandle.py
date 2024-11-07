import sys
import datetime
from scipy.signal import butter, lfilter, lfilter_zi
from PyQt5.QtWidgets import QWidget,QApplication,QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal,QObject,QDir
from time import sleep
from Ui_TCPServer import Ui_Form
import numpy as np
import threading


class Handle_Qthread_function(QObject):

    signal_start_function = pyqtSignal()
    # signal_handle_data = pyqtSignal(object) # object 是 Python 的一个基类，表示几乎所有的类都是它的子类（或它本身）。在这里，它用作 pyqtSignal 的参数类型，意味着这个信号可以传递任何 Python 对象作为参数。
    # signal_handled_a_frame = pyqtSignal(object)     # 处理完了一帧数据
    signal_handle_readyRead = pyqtSignal(object,object)
    signal_file_save_data = pyqtSignal(object)
    signal_heatMap_save_data = pyqtSignal(object)
    # signal_Engine_save_data = pyqtSignal(object)
    # signal_setEngineFlag = pyqtSignal(object)
    signal_recognitionResult = pyqtSignal(object)
    signal_showCalibrate = pyqtSignal(object)
    signal_showLineChart_be = pyqtSignal(object,object)
    signal_showLineChart_af = pyqtSignal(object,object)
    signal_caliberate_finished = pyqtSignal()
    signal_caliberate_start = pyqtSignal()
    signal_lastCaliberate = pyqtSignal()

    signal_setChartFlag = pyqtSignal(object)
    signal_setFiltFlag = pyqtSignal(object)
    signal_setCutoff = pyqtSignal(object)
    signal_setFs = pyqtSignal(object)


    def __init__(self,parent = None):
        super(Handle_Qthread_function,self).__init__(parent)   # 这里的线程依然还是主线程的ID
        self.buf = bytes()          
        self.state = 0                      # 0：未接收到帧头 1：接收到帧头 2：接收到帧尾
        self.debug = 0
        # self.engineFlag = False
        self.dataBuf = []
        self.calibrate = [0 for _ in range(20)]        # 标定值
        self.calibrateFlag = False          # False:未标定，True:已标定
        self.calibrateStart = False         # False:未开始标定，True:已开始标定
        self.motions = ['NP','DF','PF','E','IN','TD','TU','IR','ER',]

        self.chartFlag = False              # 是否显示曲线图标志位
        self.filtFlag = True                # 是否滤波标志位
        self.order = 4                      # 巴特沃斯阶数
        self.windowLen = self.order * 7     # 滤波窗口大小
        self.fs = 130                       # 采样频率
        self.cutoff = 6                     # 截止频率
        self.wn = 2 * np.array(self.cutoff) / self.fs   # 归一化截止频率
        self.B, self.A = butter(self.order, self.wn, output='ba')       # 分子分母系数向量
        self.initialState = [lfilter_zi(self.B, self.A)] * 20           # 初始状态

    def Handle_qthread_function_Init(self):
        sleep(0.5)
        print("Handle线程id:",threading.current_thread().ident)

    def slot_caliberate_start(self):
        self.calibrateStart = True         # False:未开始标定，True:已开始标定

    def slot_lastCaliberate(self):
        frame_str = ''
        with open('./标定值.txt', 'r', encoding="utf-8") as f:
            frame_str = f.read()
            self.signal_showCalibrate.emit(frame_str)

        temp = []
        head = -1
        end = -1
        flag = True # 表示该帧没问题

        for i in range(1,21):
            head = frame_str.find(f'L{i}:')
            end = frame_str.find('\n')
            if head >= 0 and end > head:
                head = frame_str.find(':') + 1
                temp.append(int(frame_str[head:end]))
                frame_str = frame_str[end + 1:]
            else:
                flag = False
                print('该标定值有误！')
                break
        if flag:
            self.calibrate = temp
            self.signal_caliberate_finished.emit()
            self.calibrateStart = False
            self.calibrateFlag = True
            # print(self.calibrate)


    # def setEngineFlag(self,flag):
    #     self.engineFlag = flag    


    # 数据处理函数
    def slot_handle_data(self,buf):
        index_head = -1
        index_end = -1
        # 待发送的数据
        frame_string = ''
        lst = []
        self.buf = self.buf + buf           

        # 数据解析
        while b'@$%' in self.buf:
            index_head = self.buf.find(b'@$%')

            # 查找帧尾
            index_end = self.buf.find(b'&\r\n')
            if index_end > 0:
                offset = 0
                temp = []
                frame_byte = self.buf[index_head + 3:index_end]     # 取出这一帧数据

                if len(frame_byte) != 40:
                    if len(frame_byte) == 1:
                        motion_str = self.motions[int.from_bytes(frame_byte, byteorder='big')]
                        self.signal_recognitionResult.emit(motion_str)

                    else:
                        print('该帧长度有误!',len(frame_byte))
                    # 更新缓存
                    self.buf = self.buf[index_end + 3:]
                    continue

                # zip函数是用来将可迭代的对象作为参数，将对象中对应的元素打包成一个个元组，然后返回由这些元组组成的对象。
                for byteH, byteL in zip(frame_byte[::2], frame_byte[1::2]):  
                    int_value = ((byteH << 8) | byteL) - self.calibrate[offset]     # 将两个字节组合成一个16位的整数（无符号）
                    temp.append(int_value)
                    offset = offset + 1
                    frame_string = frame_string + f'L{offset}:' + "{:d}".format(int_value) + '\n'

                lst.append(temp)
                
                # 更新缓存
                self.buf = self.buf[index_end + 3:]
            else:
                # self.debug = self.debug + 1
                # print('没读完',self.debug)
                # print('没读完',len(self.buf),'字节')
                break
        
        # 存储数据
        self.signal_handle_readyRead.emit(len(lst),frame_string)        # 显示原始数据

        # 正常读数
        if self.calibrateFlag == True:
            if self.filtFlag == True:
                # 滤波
                self.dataBuf.extend(lst)
                if len(self.dataBuf) >= self.windowLen:
                    arr = np.array(self.dataBuf[:self.windowLen])
                    filtered = np.empty_like(arr)
                    for col in range(arr.shape[1]):  
                        filtered[:, col], self.initialState[col] = lfilter(self.B, self.A, arr[:, col], zi=self.initialState[col])
                    # 完成滤波
                    result = filtered.tolist()          
                    # 数据分发 
                    if self.chartFlag == True:
                        self.signal_showLineChart_be.emit(self.dataBuf[:self.windowLen], self.windowLen)
                        self.signal_showLineChart_af.emit(result, self.windowLen)
                    self.dataBuf[:self.windowLen] = []
                    self.signal_file_save_data.emit(result)
                    self.signal_heatMap_save_data.emit(result)
                    # if self.engineFlag == True:
                    #     self.signal_Engine_save_data.emit(result)
            else:
                # 不滤波，直接分发数据
                if self.chartFlag == True:
                    self.signal_showLineChart_be.emit(lst, len(lst))
                self.signal_file_save_data.emit(lst)
                self.signal_heatMap_save_data.emit(lst)
                # if self.engineFlag == True:
                #     self.signal_Engine_save_data.emit(lst)

        # 标定
        elif self.calibrateStart == True:
            self.dataBuf.extend(lst)
            if len(self.dataBuf) > 600:             # 数据收集完毕
                arr = np.array(self.dataBuf)        # 列表转换为numpy数组，标定用原始数据
                col_means = np.mean(arr, axis=0)    # 按列求平均值
                self.calibrate = np.round(col_means).astype(int).tolist()   # 四舍五入，转为整形，转为列表
                self.dataBuf = []

                self.signal_caliberate_finished.emit()
                self.calibrateStart = False
                self.calibrateFlag = True

                # 保存标定值
                temp = ''
                for i in range(20):
                    temp = temp + f'L{i + 1}:' + "{:d}".format(self.calibrate[i]) + '\n'  

                file = QDir('./').filePath('标定值.txt')
                # 使用with语句，可实现在处理文件时，无论是否抛出异常，都能保证with语句执行完毕后关闭已经打开的文件。
                try:
                    with open(file,'w',encoding='utf-8') as f:
                        f.write(temp)       # with语句会确保文件关闭，因此该句可以不要
                        self.signal_showCalibrate.emit(temp)
                except IOError as e:  
                    print(f"无法创建文件: {e}")



    def slot_setChartFlag(self,flag):
        self.chartFlag = flag

    def slot_setFiltFlag(self,flag):
        self.filtFlag = flag

    def slot_setCutoff(self,cutoff):
        # self.fs = 130                       # 采样频率
        self.cutoff = cutoff                    # 截止频率
        self.wn = 2 * np.array(self.cutoff) / self.fs   # 归一化截止频率
        self.B, self.A = butter(self.order, self.wn, output='ba')       # 分子分母系数向量
        # self.initialState = [lfilter_zi(self.B, self.A)] * 20           # 初始状态

    def slot_setFs(self,fs):
        self.fs = fs                       # 采样频率
        # self.cutoff = 10                    # 截止频率
        self.wn = 2 * np.array(self.cutoff) / self.fs   # 归一化截止频率
        self.B, self.A = butter(self.order, self.wn, output='ba')       # 分子分母系数向量
        # self.initialState = [lfilter_zi(self.B, self.A)] * 20           # 初始状态






