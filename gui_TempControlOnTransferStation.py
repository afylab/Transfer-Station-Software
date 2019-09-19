# This program is to communicate with TC-720 to let a Peltier plate work as a heater/cooler, to control the vacuum chuck's temperature.

import sys
import numpy as np
import serial
import serial.tools.list_ports

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication,QMainWindow,QGridLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QListWidget, QGridLayout, QLabel
from PyQt5.QtCore import QTimer, QMutex
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ui_temp import Ui_MainWindow


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib
import matplotlib.cbook as cbook


# define a thread class for serial communication
class SerialThread(QThread):
    trigger = pyqtSignal()

    def __init__(self, portName = 'COM3', baudrate = 230400, parity = 'N', startbits = 1, stopbits = 1, timeout=None ):
        super(SerialThread, self).__init__()
        
        self.serialPort=serial.Serial()
        self.serialPort.port = portName
        self.serialPort.baudrate = baudrate
        self.serialPort.parity = parity
        self.serialPort.startbits = startbits
        self.serialPort.stopbits = stopbits
        self.serialPort.timeout = timeout
        self.OpenSerial()
    
    def OpenSerial(self):
        try:
            self.serialPort.open()
        except Exception as ex:
            print(ex)
            return ex
    
    def querySerial(self, list):
        self.bst = list
        self.serial_run()

    def serial_run(self):
        mutex.lock()
        for pn in range(0,10):
            self.serialPort.write((self.bst[pn]).encode())
        for pn in range(0,8):
            buf[pn]=self.serialPort.read(1)
        print('serial_run once')
        mutex.unlock()

        self.trigger.emit()

#define a canvas class for drawing 2D curves in GUI
class Figure_Canvas(FigureCanvas):
    def __init__(self,parent=None,width=3.9,height=2.7,dpi=100):
        self.fig=Figure(figsize=(width,height),dpi=100)
        super(Figure_Canvas,self).__init__(self.fig)
        self.ax=self.fig.add_subplot(111)
    

class MainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.setupUi(self)
        self.PrepareLineCanvas()
        
        self.timer_temp = QTimer(self)
        self.timer_temp.timeout.connect(self.Work_ReadTemp)
        self.timer_output = QTimer(self)
        self.timer_output.timeout.connect(self.Work_ReadOutput)
        
        self.connectBtn.clicked.connect(self.SerialAutoFind)
        self.startBtn.clicked.connect(lambda:self.StartTimer(self.timer_temp,2000))
        self.stopBtn.clicked.connect(lambda:self.EndTimer(self.timer_temp))
        self.okBtn_temp.clicked.connect(self.Work_SetTemp)
        self.okBtn_P.clicked.connect(self.Work_PIDsetting_P)
        self.okBtn_I.clicked.connect(self.Work_PIDsetting_I)
        self.okBtn_D.clicked.connect(self.Work_PIDsetting_D)
        self.clearBtn_temp.clicked.connect(lambda:self.ClearText(self.setTempLine))
        self.clearBtn_P.clicked.connect(lambda:self.ClearText(self.setPLine))
        self.clearBtn_I.clicked.connect(lambda:self.ClearText(self.setILine))
        self.clearBtn_D.clicked.connect(lambda:self.ClearText(self.setDLine))
        self.outputOnBtn.clicked.connect(self.Work_OutputOn)
        self.outputOnBtn.clicked.connect(lambda:self.StartTimer(self.timer_output,500))
        self.outputOffBtn.clicked.connect(self.Work_OutputOff)
        self.outputOffBtn.clicked.connect(lambda:self.EndTimer(self.timer_output))
        self.outputOffBtn.clicked.connect(lambda:self.label_readOutput.setText("      Power：0.00 %")) 
        
        self.serialthread = 0
        self.port_list = []

        self.counttime=-1

    def StartTimer(self,timerName,timeoutvalue):
        timerName.start(timeoutvalue)


    def EndTimer(self,timerName):
        timerName.stop()

    #send command to TC-720 to ask temperature
    def Work_ReadTemp(self):      
        self.serialthread.trigger.connect(self.ShowTemp)   #call the function ShowTemp()
        self.serialthread.querySerial(['*','0','1','0','0','0','0','2','1','\r'])
        self.serialthread.trigger.disconnect(self.ShowTemp)   

    #convert the str read from TC-720 into decimal temperature, unit: Celsius
    def ShowTemp(self):    
        SensorTemp=str(self.hexc2dec(buf)/100)
        if SensorTemp is not None:
            self.label_sensor.setText('      Temperature：'+SensorTemp+' ℃')
            self.LineUpdate()
        else:
            self.label_sensor.setText('Failed to read temperature')

    #set desired temperature in [0,200], unit: Celsius
    def Work_SetTemp(self):
        text_Temp=self.setTempLine.text()
        if text_Temp == '':
            QMessageBox.information(self, "Empty Text", "Please enter the desired temperature.")
        elif float(text_Temp) > 200:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0,200]')
        elif float(text_Temp) < 0:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0,200]')
        else :
            setvalue=int(float(text_Temp)*100)
            L = ['1','c'] + self.DDDD(setvalue,16)
            CmdToWrite = ['*'] + L + self.checksum(L) +['\r']
            print('SetTempCmd:',CmdToWrite)
            self.serialthread.querySerial(CmdToWrite)
            self.Work_ReadSetTemp()
    
    # send command to TC-720 to ask desired temperature setting    
    def Work_ReadSetTemp(self):
        self.serialthread.trigger.connect(self.ShowSetTemp)   #call the function ShowSetTemp()
        print('showTemp connected')
        # send command to TC-720 
        self.serialthread.querySerial(['*', '5', '0', '0', '0', '0', '0', '2', '5', '\r'])
        self.serialthread.trigger.disconnect(self.ShowSetTemp)  
        print('showSetTemp disconnected')
    
    #convert the str read from TC-720 into decimal temperature, unit: Celsius
    def ShowSetTemp(self):
        ReadSetTemp=str(self.hexc2dec(buf)/100)      
        self.readSetTemp.setText(ReadSetTemp)
    
    #Output Power On
    def Work_OutputOn(self):
        CmdToWrite = ['*', '3', '0', '0', '0', '0', '1'] + self.checksum(['3', '0', '0', '0', '0', '1']) + ['\r']
        self.serialthread.querySerial(CmdToWrite)

    #Output Power Off    
    def Work_OutputOff(self):
        CmdToWrite = ['*', '3', '0', '0', '0', '0', '0'] + self.checksum(['3', '0', '0', '0', '0', '0']) + ['\r']
        self.serialthread.querySerial(CmdToWrite)

    
    #Read output power from TC-720
    def Work_ReadOutput(self):
        self.serialthread.trigger.connect(self.ShowOutput)   #call the function ShowOutput()
        print('showoutput connected')
        self.serialthread.querySerial(['*', '0', '2', '0', '0', '0', '0', '2', '2', '\r'])
        self.serialthread.trigger.disconnect(self.ShowOutput)
        print('showoutput disconnected')        

    #convert the str read from TC-720 into decimal relative output power
    def ShowOutput(self):
        outputPower = '%.2f'%(self.hexc2dec(buf)*100/511)
        if outputPower is not None:
            self.label_readOutput.setText("      Power："+outputPower+'%')
        else:
            QMessageBox.information(self,'Error','Error when set output on/off, please try again')

    #set propotional gain(P)
    def Work_PIDsetting_P(self):
        text_P=self.setPLine.text() 
        if text_P == '':
            QMessageBox.information(self, "Empty Text", "Please enter the setting.")
        elif float(text_P) > 100:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0.05, 100]')
        elif float(text_P) < 0.05:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0.05, 100]')
        else :
            setvalue=int(float(text_P)*100)
            L = ['1','d'] + self.DDDD(setvalue,16)
            CmdToWrite = ['*'] + L + self.checksum(L) +['\r']
            print('SetPCmd:',CmdToWrite)
            self.serialthread.querySerial(CmdToWrite)
            self.Work_ReadSetP()
    
    # send command to TC-720 to ask P setting 
    def Work_ReadSetP(self):
        self.serialthread.trigger.connect(self.ShowP)
        print('showP connected')
        self.serialthread.querySerial(['*', '5', '1', '0', '0', '0', '0', '2', '6', '\r'])
        self.serialthread.trigger.disconnect(self.ShowP)
        print('showP disconnected')
        
    def ShowP(self):
        PBandwidth = str(self.hexc2dec(buf)/100)
        if PBandwidth is not None:
            self.readSetP.setText(PBandwidth)
        else:
            self.readSetP.setText('Failed to set P bandwidth')
    
    #set integral gain(I)
    def Work_PIDsetting_I(self):
        text_I=self.setILine.text()
        if text_I == '':
            QMessageBox.information(self, "Empty Text", "Please enter the setting.")
        elif float(text_I) > 10:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0.00, 10.00]')
        elif float(text_I) < 0:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0.00, 10.00]')
        else :
            setvalue=int(float(text_I)*100)
            L = ['1','e'] + self.DDDD(setvalue,16)
            CmdToWrite = ['*'] + L + self.checksum(L) +['\r']
            print('SetICmd:',CmdToWrite)
            self.serialthread.querySerial(CmdToWrite)
            self.Work_ReadSetI()

    # send command to TC-720 to ask I setting         
    def Work_ReadSetI(self):
        self.serialthread.trigger.connect(self.ShowI)
        self.serialthread.querySerial(['*', '5', '2', '0', '0', '0', '0','2','7','\r'])
        self.serialthread.trigger.disconnect(self.ShowI)

        
    def ShowI(self):
        IGain = str(self.hexc2dec(buf)/100)
        if IGain is not None:
            self.readSetI.setText(IGain)
        else:
            self.readSetI.setText('Failed to set I gain')
            
    #set derivative gain(D)        
    def Work_PIDsetting_D(self):
        text_D=self.setDLine.text()
        if text_D == '':
            QMessageBox.information(self, "Empty Text", "Please enter the setting.")
        elif float(text_D) > 10:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0.00, 10.00]')
        elif float(text_D) < 0:
            QMessageBox.information(self,'Invalid Value','Please enter a value in [0.00, 10.00]')
        else :
            setvalue=int(float(text_D)*100)
            L = ['1','f'] + self.DDDD(setvalue,16)
            CmdToWrite = ['*'] + L + self.checksum(L) +['\r']
            print('SetDCmd:',CmdToWrite)
            self.serialthread.querySerial(CmdToWrite)
            self.Work_ReadSetD()
            
    def Work_ReadSetD(self):
        self.serialthread.trigger.connect(self.ShowD)
        self.serialthread.querySerial(['*', '5', '3', '0', '0', '0', '0','2','8','\r'])
        self.serialthread.trigger.disconnect(self.ShowD)
        
    def ShowD(self):
        DGain = str(self.hexc2dec(buf)/100)
        if DGain is not None:
            self.readSetD.setText(DGain)
        else:
            self.readSetD.setText('Failed to set D gain')
            

    def ClearText(self,textName):
        if textName.text() == '':
            return
        else :
            textName.clear()
    
    #convert a list of str into a decimal value
    def hexc2dec(self,bufp):
        newval=0
        divvy=4096
        for pn in range (1,5):
            vally=ord(bufp[pn])
            if (vally < 97):
                subby=48
            else:
                subby=87
            newval+=((ord(bufp[pn])-subby)*divvy)
            divvy/=16
            if(newval > 32767):
                newval=newval-65536
        return newval
    
    #convert decimal value into list 
    def DDDD(self,val,nbits):                                 
        b=hex((val + (1 << nbits)) % (1 << nbits))
        b=b[2:]
        return list(b.zfill(4)) 

    def checksum(self,L):    
        sum=0
        for pn in range (len(L)):
            sum+= ord(L[pn])
        checksum=['%x'%(sum%256//16),'%x'%(sum%16)] 
        return checksum  

    #search and open serial
    def SerialAutoFind(self):
        #search for available ports
        self.port_list = list(serial.tools.list_ports.comports())     
        if len(self.port_list) == 0:
            QMessageBox.information(self,'Error','No Available Ports, Please Configure Device')
        else:
            comNum = len(self.port_list)
            print(str(comNum) + 'Com is found')
            while comNum:
                comNum = comNum - 1
                if "USB" in str(self.port_list[comNum]):     #port for TC-720: COM3 - USB Serial Port (COM3)
                    self.serialthread = SerialThread(portName = self.port_list[comNum][0])
                    print(str(self.port_list[comNum]) + ' is added')
                    self.Work_ReadSetTemp()
                    self.Work_ReadOutput()
                    self.Work_ReadSetP()
                    self.Work_ReadSetI()
                    self.Work_ReadSetD()

 
    def PrepareLineCanvas(self):

        self.LineFigure = Figure_Canvas()
        self.LineFigureLayout = QGridLayout(self.groupBox)
        self.LineFigureLayout.addWidget(self.LineFigure)
        self.LineFigure.ax.set_xlabel('T I M E  (s)')
        self.LineFigure.ax.set_ylabel('T E M P E R A T U R A  (℃)')
        self.LineFigure.ax.set_xlim(0, 30) 
        self.LineFigure.ax.set_ylim(0, 100) 
        self.x = []
        self.y = []
        self.line = Line2D(self.x, self.y)  
        self.LineFigure.ax.add_line(self.line)   
        
    def LineUpdate(self):
        self.counttime+=1
        self.x.append(self.counttime*2)
        self.y.append(self.hexc2dec(buf)/100)
        self.line.set_ydata(self.y)
        self.line.set_xdata(self.x)
        self.LineFigure.ax.set_xlim(0, max(30,max(self.x))) 
        self.LineFigure.ax.set_ylim(0, max(100,max(self.y))) 
        self.LineFigure.draw()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    buf=['0','0','0','0','0','0','0','0','0','0','0','0']
    mutex=QMutex()
    mainWindow.show()
    sys.exit(app.exec_())