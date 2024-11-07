import sys
from PyQt5.QtWidgets import QWidget,QApplication,QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal,QObject,QDir
from time import sleep
from Ui_TCPServer import Ui_Form
import pandas as pd
import threading


class File_Qthread_function(QObject):

    signal_start_function = pyqtSignal()
    signal_open_file = pyqtSignal(object)
    signal_set_path = pyqtSignal(object)
    signal_set_isSave = pyqtSignal(object)
    signal_set_fileName = pyqtSignal(object)
    signal_save_data = pyqtSignal(object) # object 是 Python 的一个基类，表示几乎所有的类都是它的子类（或它本身）。在这里，它用作 pyqtSignal 的参数类型，意味着这个信号可以传递任何 Python 对象作为参数。

    def __init__(self,parent = None):
        super(File_Qthread_function,self).__init__(parent)   # 这里的线程依然还是主线程的ID
        self.fileName = ''
        self.filePath = ''
        self.isSave = 0
        self.fileHead = [f'L{i}' for i in range(1,21)]
        self.realName = ''

    def File_qthread_function_Init(self):
        sleep(0.5)
        print("File线程id:",threading.current_thread().ident)

    def slot_open_file(self,isOpen):
        if self.isSave:
            if isOpen:
                print('文件名: ' + self.fileName)
                self.df = pd.DataFrame([], columns=self.fileHead)         # 保存一个空列表
                self.realName = self.filePath + '/' + self.fileName

    def slot_save_data(self,data):
        if self.isSave:
            temp = pd.DataFrame(data, columns=self.fileHead)
            self.df = self.df.append(temp)
            self.df.to_csv(self.realName, index=False)

    def slot_set_path(self,path):
        self.filePath = path
        # print('设置路径: ' + self.filePath)

    def slot_set_isSave(self,isSave):
        self.isSave = isSave
        # print('设置标志位: ' + str(self.isSave))

    def slot_set_fileName(self,fileName):
        self.fileName = fileName + '.csv'
        # print('设置文件名: ' + self.fileName)

            




