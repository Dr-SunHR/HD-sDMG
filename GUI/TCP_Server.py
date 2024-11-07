import sys
from PyQt5.QtWidgets import QWidget,QApplication
from PyQt5.QtCore import QThread, pyqtSignal,QObject
from time import sleep
from Ui_TCPServer import Ui_Form
import threading
from PyQt5.QtNetwork import QTcpServer,QHostAddress

class TCP_Server_Qthread_function(QObject):

    signal_start_function = pyqtSignal()
    signal_pushButton_open = pyqtSignal(object) # object 是 Python 的一个基类，表示几乎所有的类都是它的子类（或它本身）。在这里，它用作 pyqtSignal 的参数类型，意味着这个信号可以传递任何 Python 对象作为参数。
    signal_pushButton_open_flag = pyqtSignal(object)
    signal_readyRead = pyqtSignal(object)
    signal_newClient = pyqtSignal(object)
    signal_closeClient = pyqtSignal(object)
    signal_sendData = pyqtSignal(object)

    def __init__(self,parent=None):
        super(TCP_Server_Qthread_function,self).__init__(parent)   # 这里的线程依然还是主线程的ID
        #开始调用网络的信号
        self.state = 0  # 0未打卡，1已打开，2关闭
        self.listClient = []    # 列表，保存客户端
        self.newClient = []
        self.newClient.insert(0,'All Connections(' + str(len(self.listClient)) + ')')
        self.debug = 0


    # 槽函数，发送数据
    def slot_sendData(self,parameter):
        # print("UDP发送数据",parameter)
        if self.state != 1:
            return
        # self.signal_sendData_Num.emit(len(parameter['data']))

        if parameter['ip_port'].find('All Connections') >= 0:      # 如果找到这个字符串，表示给所有客户端发送
            for i in range(len(self.listClient)):
                self.listClient[i].write(parameter['data'])
        else:       # 表示给某个具体客户端发送
            for i in range(len(self.listClient)):
                ip = self.listClient[i].peerAddress().toString()
                port = self.listClient[i].peerPort()
                ip_port = ip + ':' + str(port)
                if parameter['ip_port'] == ip_port:
                    self.listClient[i].write(parameter['data'])


    def TCP_Server_qthread_function_Init(self):
        # sleep(1.5)
        # print("TCP_Server线程id:",threading.current_thread().ident)
        self.tcpserver = QTcpServer()
        self.tcpserver.newConnection.connect(self.newConnection)


    # 槽函数，更新list
    def updateState(self):
        # print("更新listClient")
        for i in range(len(self.listClient)):
            if self.listClient[i].state() == 0:
                del self.listClient[i]      # 客户端断开连接时，删除其list
                break


    def newConnection(self):
        tcpClient = self.tcpserver.nextPendingConnection()  # 服务器可能会同时接收到多个连接请求，但并不是所有的连接都会立即被处理。那些尚未被处理的连接请求会被放入一个队列中，等待服务器处理。.nextPendingConnection() 方法就是从这个队列中取出下一个等待处理的连接请求，并返回一个与之关联的 QTcpSocket 对象，以便进行后续的通信。
        print("新建连接",tcpClient.peerAddress().toString(), tcpClient.peerPort())
        tcpClient.readyRead.connect(self.slot_readyRead)
        tcpClient.disconnected.connect(self.updateState)
        self.listClient.append(tcpClient)
        del self.newClient[0]
        self.newClient.insert(0,'All Connections(' + str(len(self.listClient)) + ')')
        self.newClient.append(tcpClient.peerAddress().toString() + ':' + str(tcpClient.peerPort()))
        self.signal_newClient.emit(self.newClient)


    def slot_closeClient(self,parameter):
        # print('TCP Server断开',parameter)
        if parameter.find('All Connections') >= 0:      # 如果找到这个字符串，表示删除所有客户端
            for i in range(len(self.listClient)):
                self.listClient[i].disconnected.disconnect(self.updateState)    # 断开信号与槽的连接
                self.listClient[i].readyRead.disconnect(self.slot_readyRead)    # 断开信号与槽的连接
                self.listClient[i].close()
            self.newClient.clear()
            self.listClient.clear()
            # 更新显示
            self.newClient.insert(0,'All Connections(' + str(len(self.listClient)) + ')')
            self.signal_newClient.emit(self.newClient)
        else:           # 删除某个具体的客户端
            for i in range(len(self.listClient)):
                ip = self.listClient[i].peerAddress().toString()
                port = self.listClient[i].peerPort()
                ip_port = ip + ':' + str(port)
                if parameter == ip_port:
                    self.listClient[i].disconnected.disconnect(self.updateState)    # 断开信号与槽的连接
                    self.listClient[i].readyRead.disconnect(self.slot_readyRead)    # 断开信号与槽的连接
                    self.listClient[i].close()
                    del self.listClient[i]
                    self.newClient.remove(ip_port)
                    del self.newClient[0]
                    self.newClient.insert(0,'All Connections(' + str(len(self.listClient)) + ')')
                    self.signal_newClient.emit(self.newClient)
                    return


    # 槽函数：接收函数
    def slot_readyRead(self):
        # print("收到数据")
        for i in range(len(self.listClient)):
            if self.listClient[i].bytesAvailable() > 0:
                buf = self.listClient[i].readAll()
                
                self.signal_readyRead.emit(bytes(buf))      # buf 的类型是QByteArray
                # self.debug = self.debug + 1
                # print('TCP 收到数据',self.debug)


    def slot_pushButton_open(self,parameter):
        # print("打开TCP Server",parameter)
        if self.state == 0:
            # 强转格式为地址格式
            # 监听端口信号，成功返回true，失败返回false
            if self.tcpserver.listen(QHostAddress(parameter['ip']),int(parameter['port'])):  
                self.state = 1
                self.signal_pushButton_open_flag.emit(1)
            else:
                self.signal_pushButton_open_flag.emit(0)
            self.signal_newClient.emit(self.newClient)
        else:
            for i in range(len(self.listClient)):
                self.listClient[i].disconnected.disconnect(self.updateState)    # 断开信号与槽的连接
                self.listClient[i].readyRead.disconnect(self.slot_readyRead)    # 断开信号与槽的连接
                self.listClient[i].close()
            self.listClient.clear()
            self.tcpserver.close()
            self.state = 0
            self.signal_pushButton_open_flag.emit(2)
            self.newClient.clear()
            self.newClient.insert(0,'All Connections(' + str(len(self.listClient)) + ')')
            self.signal_newClient.emit(self.newClient)




