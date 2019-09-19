from TransferStation import *
from XboxController import *

import clr
clr.AddReference("PresentationFramework.Classic, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35")
clr.AddReference("PresentationCore, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35")
clr.AddReference("System.Windows.Forms")

from System.Windows import Application, Window
from System.Windows import MessageBox, MessageBoxButton, MessageBoxImage, MessageBoxResult
from System.Windows import LogicalTreeHelper
from System.IO import StreamReader
from System.Windows.Markup import XamlReader
from System.Threading import Thread, ApartmentState, ThreadStart
from System.Windows.Threading import DispatcherTimer
from System import *
from time import sleep

Transfer = TransferStation()

set_deadzone(DEADZONE_TRIGGER, 10)

rx_moving = STOP
ry_moving = STOP
x_moving = STOP
y_moving = STOP
running = True
status = {'x' : x_moving, 'y' : y_moving, 'rx' : rx_moving, 'ry' : ry_moving}

class MainWindow(Window):
    def __init__(self):
        '''
        get the window design from Window.xaml
        FindLogicalNode maps each component to a variable
        += maps an event to a function, the name of the event can be found in Windows class help file
        '''
        Window.__init__(self)

        stream = StreamReader("Window.xaml")
        window = XamlReader.Load(stream.BaseStream)

        self._timer = DispatcherTimer()
        self._timer.Tick += self._timer_Tick
        self._timer.Interval = TimeSpan.FromMilliseconds(10) 'run the timer every 10ms'
        self._timer.Start()

        initializing = True
        print("main window")
        while Transfer.all_connected() == False and initializing:
            if MessageBox.Show("Devices not initialized, retry?","warning", MessageBoxButton.YesNo, MessageBoxImage.Information) == MessageBoxResult.Yes:
                Transfer.reinitialize()
            else:
                initializing = False

        if initializing == False:
            Application.Current.Shutdown()
            return

        self.UI_x = LogicalTreeHelper.FindLogicalNode(window, "UI_x")
        self.UI_x.Content = KCubeDCServoUI.CreateLargeView(Transfer.x)
        self.UI_y = LogicalTreeHelper.FindLogicalNode(window, "UI_y")
        self.UI_y.Content = KCubeDCServoUI.CreateLargeView(Transfer.y)
        self.UI_z = LogicalTreeHelper.FindLogicalNode(window, "UI_z")
        self.UI_z.Content = KCubeDCServoUI.CreateLargeView(Transfer.z)
        self.UI_rx = LogicalTreeHelper.FindLogicalNode(window, "UI_rx")
        self.UI_rx.Content = KCubeDCServoUI.CreateLargeView(Transfer.rx)
        self.UI_ry = LogicalTreeHelper.FindLogicalNode(window, "UI_ry")
        self.UI_ry.Content = KCubeDCServoUI.CreateLargeView(Transfer.ry)
        self.UI_r = LogicalTreeHelper.FindLogicalNode(window, "UI_r")
        self.UI_r.Content = KCubeDCServoUI.CreateLargeView(Transfer.r)

        self.Help = LogicalTreeHelper.FindLogicalNode(window, "Help")
        self.Help.Click += self.Help_Click

        self.ZUp = LogicalTreeHelper.FindLogicalNode(window, "ZUp")
        self.ZUp.Checked += self.ZUp_Checked
        self.ZUp.Unchecked += self.ZUp_Unchecked
        self.ZDown = LogicalTreeHelper.FindLogicalNode(window, "ZDown")
        self.ZDown.Checked += self.ZDown_Checked
        self.ZDown.Unchecked += self.ZDown_Unchecked

        self.ViewMode = LogicalTreeHelper.FindLogicalNode(window, "ViewMode")
        self.ViewMode.SelectionChanged += self.ViewMode_Changed

        self.Button1 = LogicalTreeHelper.FindLogicalNode(window, "Button1")
        self.Button1.Click += self.Button1_Click

        self.Mode = LogicalTreeHelper.FindLogicalNode(window, "Mode")
        self.Mode.Text = "High speed mode"

        self.RotateAngle = LogicalTreeHelper.FindLogicalNode(window, "Angle")

        self.Title = "Gaming..."
        '''lock the size'''

        Application().Run(window)

    def ViewMode_Changed(self, sender, e):
        if self.ViewMode.SelectedValue.Name == "SimpleMode":
            self.UI_x.Content = KCubeDCServoUI.CreateSmallView(Transfer.x)
            self.UI_y.Content = KCubeDCServoUI.CreateSmallView(Transfer.y)
            self.UI_z.Content = KCubeDCServoUI.CreateSmallView(Transfer.z)
            self.UI_rx.Content = KCubeDCServoUI.CreateSmallView(Transfer.rx)
            self.UI_ry.Content = KCubeDCServoUI.CreateSmallView(Transfer.ry)
            self.UI_r.Content = KCubeDCServoUI.CreateSmallView(Transfer.r)
        if self.ViewMode.SelectedValue.Name == "ComplexMode":
            self.UI_x.Content = KCubeDCServoUI.CreateLargeView(Transfer.x)
            self.UI_y.Content = KCubeDCServoUI.CreateLargeView(Transfer.y)
            self.UI_z.Content = KCubeDCServoUI.CreateLargeView(Transfer.z)
            self.UI_rx.Content = KCubeDCServoUI.CreateLargeView(Transfer.rx)
            self.UI_ry.Content = KCubeDCServoUI.CreateLargeView(Transfer.ry)
            self.UI_r.Content = KCubeDCServoUI.CreateLargeView(Transfer.r)
        self.SizeToContent = True

    def Button1_Click(self, sender, e):
        try:
            angle = float(self.RotateAngle.Text)
            Transfer.rotate(angle)
        except ValueError:
            MessageBox.Show("Input invalid")
        self.RotateAngle.Clear()

    def _timer_Tick(self, sender, e):
        '''
        keeps running to get the command and control.
        event is the signal from Xbox controller
        '''
        #Transfer.check()\
        #print("for/bavk/stop:{0}{1}{2}".format(Transfer.rx.Status.IsMovingForward, Transfer.rx.Status.IsMovingBackward, Transfer.rx.Status.IsMoving))
        events = get_events()
        for event in events:
            if event.type == EVENT_BUTTON_RELEASED and event.button == "BACK":
                Transfer.close()
            if event.type == EVENT_BUTTON_RELEASED and event.button == "START":
                Transfer.__init__()
                #self.__init__() !!!!
            if event.type == EVENT_BUTTON_PRESSED and event.button == "LEFT_SHOULDER":
                if self.Mode.Text == "Low speed mode":
                    Transfer.setspeed([200000, 500000, 25000, 300000])
                    self.Mode.Text = "High speed mode"
                else:
                    Transfer.setspeed([20000, 20000, 2500, 5000])
                    self.Mode.Text = "Low speed mode"
                print(Transfer.speed)
            WrongInfo = Transfer.move(event)
            if WrongInfo != 'None':
                MessageBox.Show(WrongInfo)

    def ZUp_Checked(self, sender, e):
        '''
        the function for the checkbox (the switch of z up/down)
        '''
        if self.ZDown.IsChecked == True:
            try:
                Transfer.z.Stop(0)
            except:
                pass
            sleep(0.5)
            self.ZDown.IsChecked = False
        Transfer.z.MoveContinuousAtVelocity(FORWARD, 500)

    def ZUp_Unchecked(self, sender, e):
        Transfer.z.Stop(0)

    def ZDown_Checked(self, sender, e):
        if self.ZUp.IsChecked == True:
            try:
                Transfer.z.Stop(0)
            except:
                pass
            sleep(0.5)
            self.ZUp.IsChecked = False
        Transfer.z.MoveContinuousAtVelocity(BACKWARD, 500)

    def ZDown_Unchecked(self, sender, e):
        Transfer.z.Stop(0)

    def Help_Click(self, sender, e):
        '''
        can show a help file after clicking the help
        '''
        pass

thread = Thread(ThreadStart(MainWindow))
thread.SetApartmentState(ApartmentState.STA)
thread.Start()
thread.Join()
Transfer.close()
'''
exception message should be update
check the forward and backwared limit
'''