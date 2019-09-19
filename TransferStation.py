import clr
import sys
from XboxController import *
from System.Collections import *
from System import Decimal
from time import sleep

sys.path.append(r"C:\Program Files\Thorlabs\Kinesis")

clr.AddReference("Thorlabs.MotionControl.KCube.DCServoUI")
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI")
clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
from Thorlabs.MotionControl.KCube.DCServoUI import *
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.KCube.DCServoCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
'''This might change, check!'''
serial_461_x="27253801"
serial_461_y='27254302'
serial_461_z='27254296'
serial_rot_x='27254303'
serial_rot_y='27254066'
serial_rotation='27003766'

#some notification for xbox didnot connect

#MotorDirection - Forward/Backward according to help file, Stop defined by myself
FORWARD = 0x01 #number get bigger
BACKWARD = 0x02#number get smaller
STOP = 0x00 #I define it, not in the help file
JOYSTICKSPEED_STAGE = 20000
JOYSTICKSPEED_ROTATE = 20000
Z_SPEED = 500
ROTATE_SPEED = 5000
'''device.SetJogStepSize(Decimal(0.05))'''
JOGSTEP_MOVE = Decimal(0.0005) #in mm
JOGSTEP_RTATE = Decimal(1)  #in degree

class TransferStation(object):
    def __initialize(self, serialNo):
        '''
        make connection to a device(you need to build a devicelist first before you make connection to a single device)
		return the device created
        '''
        device = KCubeDCServo.CreateKCubeDCServo(serialNo)
        try:
            device.Connect(serialNo)
            device.LoadMotorConfiguration(serialNo)
            device.WaitForSettingsInitialized(5000)
            deviceInfo = device.GetDeviceInfo()
            print(deviceInfo.Name, 'connected', deviceInfo.SerialNumber)
            #device.StartPolling(25)
            #device.Home(60000)
        except:
            print('something wrong with: ', serialNo)
        device.moving = STOP
        return device

    def __init__(self):
        '''
        make devicelist and connect all devices
        '''
        DeviceManagerCLI.BuildDeviceList()
        self.x = self.__initialize(serial_461_x)
        self.y = self.__initialize(serial_461_y)
        self.z = self.__initialize(serial_461_z)
        self.rx = self.__initialize(serial_rot_x)
        self.ry = self.__initialize(serial_rot_y)
        self.r = self.__initialize(serial_rotation)
        #for device in [self.x, self.y, self.rx, self.ry]:
        #device.MoveTo_DeviceUnit(device.MotorPositionLimits.MaxValue / 2, 0)
        sleep(2)
        self.setspeed([200000, 500000, 25000, 300000])
        print(self.speed)
        '''
        can let them move to the "center" position
        '''
    def reinitialize(self):#test i am not sure wether i need to build the devicelist again, maybe not
        if self.x.IsConnected != True:
            self.x = self.__initialize(serial_461_x)
        if self.y.IsConnected != True:
            self.y = self.__initialize(serial_461_y)
        if self.z.IsConnected != True:
            self.z = self.__initialize(serial_461_z)
        if self.rx.IsConnected != True:
            self.rx = self.__initialize(serial_rot_x)
        if self.ry.IsConnected != True:
            self.ry = self.__initialize(serial_rot_y)
        if self.r.IsConnected != True:
            self.r = self.__initialize(serial_rotation)


    def setparameters(self, parameters):
        '''
        jog step/move speed
        one button chage high speed mode and low speed mode
        '''


    def close(self):
        for device in [self.x, self.y, self.z, self.rx, self.ry, self.r]:
            device.StopPolling()
            device.Disconnect(True)
        print('Disconnected')

    def __movedirection(self, joystickvalue, status):
        '''
        value>0 backward;value<0 forward
        '''
        deadzone = 0.5
        if joystickvalue > deadzone and status != BACKWARD:
            return BACKWARD
        if joystickvalue < -deadzone and status != FORWARD:
            return FORWARD
        if joystickvalue < deadzone and joystickvalue > -deadzone and status != STOP:
            return STOP

    def setspeed(self, parameters):
        self.speed = parameters

    def rotate(self, angle):
        pos = float(str(self.r.Position))
        new_pos = Decimal((pos + angle) % 360)
        print(new_pos)
        self.r.MoveTo(new_pos, 0)

    def move(self, event):
        alert_message = 'None'
        if event.type == EVENT_CONNECTED:
            pass

        elif event.type == EVENT_DISCONNECTED:
            pass

        elif event.type == EVENT_STICK_MOVED:
            if event.stick == LEFT:
                if self.__movedirection(event.x, self.rx.moving) == FORWARD:'to inverse the direction you can change the joystick value to -event.x'
                    try:
                        self.rx.MoveContinuousAtVelocity(FORWARD, self.speed[1])
                        self.rx.moving = FORWARD
                    except Exception:
                        alert_message = 'rx will end up in invalid position!!'

                elif self.__movedirection(event.x, self.rx.moving) == BACKWARD:
                    try:
                        self.rx.MoveContinuousAtVelocity(BACKWARD, self.speed[1])
                        self.rx.moving = BACKWARD
                    except Exception:
                        alert_message = 'rx will end up in invalid position!!'
                elif self.__movedirection(event.x, self.rx.moving) == STOP:
                    self.rx.Stop(0)
                    self.rx.moving = STOP

                '''ry moves in a reversal direction, don't get messed up with the __movedirection()'''
                if self.__movedirection(-event.y, self.ry.moving) == FORWARD:
                    try:
                        self.ry.MoveContinuousAtVelocity(FORWARD, self.speed[1])
                        self.ry.moving = FORWARD
                    except Exception:
                        alert_message = 'ry will end up in invalid position!!'
                elif self.__movedirection(-event.y, self.ry.moving) == BACKWARD:
                    try:
                        self.ry.MoveContinuousAtVelocity(BACKWARD, self.speed[1])
                        self.ry.moving = BACKWARD
                    except Exception:
                        alert_message = 'ry will end up in invalid position!!'
                elif self.__movedirection(-event.y, self.ry.moving) == STOP:
                    self.ry.Stop(0)
                    self.ry.moving = STOP


            elif event.stick == RIGHT:
                if self.__movedirection(event.x, self.x.moving) == FORWARD:
                    try:
                        self.x.MoveContinuousAtVelocity(FORWARD,
                                                        self.speed[0])
                        self.x.moving = FORWARD
                    except Exception:
                        alert_message = 'x will end up in invalid position!!'
                elif self.__movedirection(event.x, self.x.moving) == BACKWARD:
                    try:
                        self.x.MoveContinuousAtVelocity(BACKWARD, self.speed[0])
                        self.x.moving = BACKWARD
                    except Exception:
                        alert_message = 'x will end up in invalid position!!'
                elif self.__movedirection(event.x, self.x.moving) == STOP:
                    self.x.Stop(0)
                    self.x.moving = STOP

                if self.__movedirection(event.y, self.y.moving) == FORWARD:
                    try:
                        self.y.MoveContinuousAtVelocity(BACKWARD, self.speed[0])
                        self.y.moving = FORWARD
                    except Exception:
                        alert_message = 'y will end up in invalid position!!'
                        print(Exception)
                elif self.__movedirection(event.y, self.y.moving) == BACKWARD:
                    try:
                        self.y.MoveContinuousAtVelocity(FORWARD, self.speed[0])
                        self.y.moving = BACKWARD
                    except Exception:
                        alert_message = 'y will end up in invalid position!!'
                elif self.__movedirection(event.y, self.y.moving) == STOP:
                    self.y.Stop(0)
                    self.y.moving = STOP


        elif event.type == EVENT_TRIGGER_MOVED:
            if event.trigger == LEFT:
                pass
            elif event.trigger == RIGHT:
                pass

        elif event.type == EVENT_BUTTON_PRESSED:
            if event.button == "RIGHT_SHOULDER":
                if self.rx.Status.IsEnabled:
                    self.rx.DisableDevice()
                    self.ry.DisableDevice()
                    self.x.DisableDevice()
                    self.y.DisableDevice()
                    print("Disabled")
                else:
                    self.rx.EnableDevice()
                    self.ry.EnableDevice()
                    self.x.EnableDevice()
                    self.y.EnableDevice()
                    print("Enabled")
                sleep(0.2)
            elif event.button == "LEFT_SHOULDER":
                pass
            elif event.button == "LEFT_THUMB":
                pass
            elif event.button == "RIGHT_THUMB":
                pass


            elif event.button == "A":
                try:
                    self.z.MoveContinuousAtVelocity(BACKWARD, self.speed[2])
                except Exception as ex:
                    alert_message = 'z will end up in invalid position!!'

            elif event.button == "B":
                try:
                    self.r.MoveContinuousAtVelocity(FORWARD, self.speed[3])
                except Exception as ex:
                    alert_message = 'e...something wrong with the rotation'
            elif event.button == "Y":
                try:
                    self.z.MoveContinuousAtVelocity(FORWARD, self.speed[2])
                except Exception as ex:
                    alert_message = 'z will end up in invalid position!!'

            elif event.button == "X":
                try:
                    self.r.MoveContinuousAtVelocity(BACKWARD, self.speed[3])
                except Exception as ex:
                    alert_message = 'e...something wrong with the rotation'

        elif event.type == EVENT_BUTTON_RELEASED:
            if event.button == "LEFT_THUMB":
                pass
            elif event.button == "RIGHT_THUMB":
                pass


            elif event.button == "DPAD_LEFT":
                try:
                    self.x.MoveJog(BACKWARD, 0)
                except Exception:
                    alert_message = 'x will end up in invalid position!!'
            elif event.button == "DPAD_RIGHT":
                try:
                    self.x.MoveJog(FORWARD, 0)
                except Exception:
                    alert_message = 'x will end up in invalid position!!'
            elif event.button == "DPAD_UP":
                try:
                    self.y.MoveJog(BACKWARD, 0)
                except Exception:
                    alert_message = 'y will end up in invalid position!!'
            elif event.button == "DPAD_DOWN":
                try:
                    self.y.MoveJog(FORWARD, 0)
                except Exception:
                    alert_message = 'y will end up in invalid position!!'

            elif event.button == "A":
                self.z.Stop(0)
            elif event.button == "B":
                self.r.Stop(0)
            elif event.button == "Y":
                self.z.Stop(0)
            elif event.button == "X":
                self.r.Stop(0)

        return alert_message

    def check(self):
        '''check that all the atuators did not reach their limit and are homed'''
        pass

    def all_connected(self):
        try:
            return self.x.IsConnected and self.y.IsConnected and self.z.IsConnected and self.rx.IsConnected and self.ry.IsConnected and self.r.IsConnected
        except:
            return False

'''
how to MoveTO?
LoadMotorConfigurationFirst
.MoveTo(Decimal(pos), time)
time= timeout limit
pos/mm
'''