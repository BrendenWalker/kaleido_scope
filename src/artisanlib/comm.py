#
# ABOUT
# Artisan Device Communication

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

import sys
import time as libtime
import platform
import logging
from collections.abc import Callable
from typing import Final, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    import serial # noqa: F401 # pylint: disable=unused-import

from artisanlib.util import str2cmd

from PyQt6.QtCore import Qt, QSemaphore, pyqtSlot
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout, QHBoxLayout, QVBoxLayout,
                             QLabel, QLineEdit,QPushButton, QWidget)
from PyQt6 import sip


_log: Final[logging.Logger] = logging.getLogger(__name__)


#########################################################################
#############  NONE DEVICE DIALOG #######################################
#########################################################################

#inputs temperature
class nonedevDlg(QDialog):

    __slots__ = ['etEdit','btEdit','ETbox','okButton','cancelButton'] # save some memory by using slots

    def __init__(self, parent:QWidget, aw:'ApplicationWindow') -> None:
        super().__init__(parent)

        self.aw = aw

        self.setWindowTitle(QApplication.translate('Form Caption','Manual Temperature Logger'))
        if len(self.aw.qmc.timex):
            if self.aw.qmc.manuallogETflag:
                etval = str(int(round(aw.qmc.temp1[-1])))
            else:
                etval = '0'
            btval = str(int(round(aw.qmc.temp2[-1])))
        else:
            etval = '0'
            btval = '0'
        self.etEdit = QLineEdit(etval)
        btlabel = QLabel(QApplication.translate('Label', 'BT'))
        self.btEdit = QLineEdit(btval)
        self.etEdit.setValidator(QIntValidator(0, 1000, self.etEdit))
        self.btEdit.setValidator(QIntValidator(0, 1000, self.btEdit))
        self.btEdit.setFocus()
        self.ETbox = QCheckBox(QApplication.translate('CheckBox','ET'))
        if self.aw.qmc.manuallogETflag:
            self.ETbox.setChecked(True)
        else:
            self.ETbox.setChecked(False)
            self.etEdit.setVisible(False)
        self.ETbox.stateChanged.connect(self.changemanuallogETflag)
        self.okButton = QPushButton(QApplication.translate('Button','OK'))
        self.cancelButton = QPushButton(QApplication.translate('Button','Cancel'))
        self.cancelButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.okButton)
        grid = QGridLayout()
        grid.addWidget(self.ETbox,0,0)
        grid.addWidget(self.etEdit,0,1)
        grid.addWidget(btlabel,1,0)
        grid.addWidget(self.btEdit,1,1)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(grid)
        mainLayout.addStretch()
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

    @pyqtSlot(int)
    def changemanuallogETflag(self, _:int) -> None:
        if self.ETbox.isChecked():
            self.aw.qmc.manuallogETflag = 1
            self.etEdit.setVisible(True)
            self.etEdit.setFocus()
        else:
            self.aw.qmc.manuallogETflag = 0
            self.etEdit.setVisible(False)
            self.btEdit.setFocus()


###########################################################################################
##################### SERIAL PORT #########################################################
###########################################################################################

class serialport:
    """ this class handles the communications with all the devices"""

    __slots__ = ['aw', 'platf', 'default_comport', 'comport','baudrate','bytesize','parity','stopbits','timeout','SP','COMsemaphore', \
        'controlETpid','readBTpid','useModbusPort','showFujiLCDs','arduinoETChannel','arduinoBTChannel','arduinoATChannel',\
        'ArduinoIsInitialized','ArduinoFILT','R1','devicefunctionlist','externalprogram',\
        'externaloutprogram','externaloutprogramFlag']

    def __init__(self, aw:'ApplicationWindow') -> None:

        self.aw = aw

        self.platf = platform.system()

        #default initial settings. They are changed by settingsload() at initiation of program according to the device chosen
        self.default_comport:Final[str] = 'COM4'
        self.comport:str = self.default_comport      #NOTE: this string should not be translated. It is an argument for lib Pyserial
        self.baudrate:int = 9600
        self.bytesize:int = 8
        self.parity:str = 'O'
        self.stopbits:int = 1
        self.timeout:float = 0.4
        #serial port for ET/BT
        import serial  # @UnusedImport
        self.SP:serial.Serial = serial.Serial()
        #used only in devices that also control the roaster like PIDs or Arduino (possible to receive asynchrous commands from GUI commands and thread sample()).
        self.COMsemaphore:QSemaphore = QSemaphore(1)
        #select PID type that controls the roaster.
        # Reads/Controls ET
        self.controlETpid:list[int] = [0,1]        # index 0: type of pid: 0 = FujiPXG, 1 = FujiPXR3, 2 = DTA, 3 = not used, 4 = PXF
#                                                  # index 1: RS485 unitID: Can be changed in device menu.
        # Reads BT
        self.readBTpid:list[int] = [1,2]           # index 0: type of pid: 0 = FujiPXG, 1 = FujiPXR3, 2 = None, 3 = DTA, 4 = PXF
#                                                  # index 1: RS485 unitID. Can be changed in device menu.
        # Reuse Modbus-meter port
        self.useModbusPort:bool = False
        self.showFujiLCDs:bool = True
        #Initialization for ARDUINO and TC4 meter (kept so settings load does not AttributeError)
        self.arduinoETChannel:str = '1'
        self.arduinoBTChannel:str = '2'
        self.arduinoATChannel = 'None' # the channel the Ambient Temperature of the Arduino TC4 is reported as (this value will overwrite the corresponding real channel)
        self.ArduinoIsInitialized = 0
        self.ArduinoFILT = [70,70,70,70] # Arduino Filter settings per channel in %
        self.R1:Any = None
        #list of functions calls to read temperature for devices.
        # Device IDs 0..206 must remain the same length. Unused IDs map to DUMMY.
        # Keep-set: 18 NONE, 22 piddutycycle, 25 virtual, 50 DUMMY,
        # 90 slider_01, 91 slider_23, 138 Kaleido_BTET, 139 Kaleido_SVAT,
        # 140 Kaleido_DrumAH, 141 Kaleido_HeaterFan, 177 pidPtermIterm, 178 pidDtermError
        self.devicefunctionlist:list[Callable[..., tuple[float,float,float]]] = [self.DUMMY] * 207
        self.devicefunctionlist[18] = self.NONE
        self.devicefunctionlist[22] = self.piddutycycle
        self.devicefunctionlist[25] = self.virtual
        self.devicefunctionlist[90] = self.slider_01
        self.devicefunctionlist[91] = self.slider_23
        self.devicefunctionlist[138] = self.Kaleido_BTET
        self.devicefunctionlist[139] = self.Kaleido_SVAT
        self.devicefunctionlist[140] = self.Kaleido_DrumAH
        self.devicefunctionlist[141] = self.Kaleido_HeaterFan
        self.devicefunctionlist[177] = self.pidPtermIterm
        self.devicefunctionlist[178] = self.pidDtermError
        #string with the name of the program for device #27
        self.externalprogram:str = 'test.py'
        self.externaloutprogram:str = 'out.py' # this program is called with arguments <ET>,<BT>,<ETB>,<BTB> values on each sampling
        self.externaloutprogramFlag:bool = False # if true the externaloutprogram will be called on each sample()

#####################  FUNCTIONS  ############################
    #especial function that collects extra duty cycle % and SV
    def piddutycycle(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        if self.aw.qmc.device == 0: # FUJI
            #return saved readings from device 0
            return self.aw.qmc.dutycycleTX, self.aw.qmc.dutycycle, self.aw.qmc.currentpidsv
        if not self.aw.pidcontrol.pidActive:
            self.aw.qmc.updateLargePIDLCDs(sv='', duty='')
            return self.aw.qmc.timeclock.elapsedMilli(),-1,-1
        lcdformat = ('%.1f' if self.aw.qmc.LCDdecimalplaces else '%.0f')
        if (self.aw.qmc.device == 19 and not self.aw.pidcontrol.externalPIDControl()) or \
                (self.aw.qmc.device in {29, 79} and not self.aw.pidcontrol.externalPIDControl()):
                # TC4 (19) or MODBUS/S7 (29/79) with Artisan Software PID
            duty = self.aw.qmc.pid.getDuty()
            duty = (-1.0 if duty is None else min(100.0, max(-100.0, duty)))
            self.aw.qmc.updateLargePIDLCDs(sv=lcdformat%self.aw.qmc.pid.target, duty=lcdformat%duty)
            return self.aw.qmc.timeclock.elapsedMilli(), duty, self.aw.qmc.pid.target
        sv = self.aw.pidcontrol.sv if self.aw.pidcontrol.sv is not None else -1
        if self.aw.qmc.device == 29: # external MODBUS PID
            duty = -1
        else:
            duty = self.aw.qmc.pid.getDuty()
            duty = (-1.0 if duty is None else min(100.0, max(-100.0, duty)))
        self.aw.qmc.updateLargePIDLCDs(sv=lcdformat%sv, duty=lcdformat%duty)
        return tx, duty, sv

    def pidPtermIterm(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        return tx, self.aw.qmc.pid.getIterm(), self.aw.qmc.pid.getPterm()

    def pidDtermError(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        return tx, self.aw.qmc.pid.getError(), self.aw.qmc.pid.getDterm()

    def slider_01(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        t1 = self.aw.slider1.value()
        t2 = self.aw.slider2.value()
        return tx,t2,t1

    def slider_23(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        t1 = self.aw.slider3.value()
        t2 = self.aw.slider4.value()
        return tx,t2,t1

    def virtual(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        return tx,1.,1.

    def DUMMY(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        return tx,0,0

    def NONE(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        t2,t1 = self.NONEtmp()
        return tx,t2,t1

    def Kaleido_BTET(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        t1:float = -1
        t2:float = -1
#        _sid:int = 0
        if self.aw.kaleido is not None:
            t1, t2, _sid = self.aw.kaleido.getBTET()
# it remains unclear what those machine exactly report and when. In some cases processingn this event flag can lead to unfavorable situations so we do not process them at all
# now the syncing of those event flags can be user configurable and is by default OFF
            if self.aw.qmc.flagstart:
                try:
                    event_flag:int = _sid & 15 # last 4 bits of the sid
                    if len(self.aw.kaleidoEventFlags)>0 and self.aw.kaleidoEventFlags[0] and event_flag == 1 and self.aw.qmc.timeindex[0] == -1:
                        self.aw.qmc.markChargeSignal.emit(True) # CHARGE
    #                elif event_flag == 2 and self.aw.qmc.TPalarmtimeindex is None:
    #                    self.aw.qmc.markTPSignal.emit() # TP
                    elif len(self.aw.kaleidoEventFlags)>1 and self.aw.kaleidoEventFlags[1] and event_flag == 3 and self.aw.qmc.timeindex[1] == 0:
                        self.aw.qmc.markDRYSignal.emit(True) # DRY
                    elif len(self.aw.kaleidoEventFlags)>2 and self.aw.kaleidoEventFlags[2] and event_flag == 4 and self.aw.qmc.timeindex[2] == 0:
                        self.aw.qmc.markFCsSignal.emit(True) # FCs
                    elif len(self.aw.kaleidoEventFlags)>3 and self.aw.kaleidoEventFlags[3] and event_flag == 5 and self.aw.qmc.timeindex[3] == 0:
                        self.aw.qmc.markFCeSignal.emit(True) # FCe
                    elif len(self.aw.kaleidoEventFlags)>4 and self.aw.kaleidoEventFlags[4] and event_flag == 6 and self.aw.qmc.timeindex[4] == 0:
                        self.aw.qmc.markSCsSignal.emit(True) # SCs
                    elif len(self.aw.kaleidoEventFlags)>5 and self.aw.kaleidoEventFlags[5] and event_flag == 7 and self.aw.qmc.timeindex[5] == 0:
                        self.aw.qmc.markSCeSignal.emit(True) # SCe
                    elif len(self.aw.kaleidoEventFlags)>6 and self.aw.kaleidoEventFlags[6] and (event_flag == 8 and self.aw.qmc.timeindex[6] == 0 and
                        self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.autoDropIdx == 0 and
                        (self.aw.qmc.timex[-1] - self.aw.qmc.timex[self.aw.qmc.timeindex[0]]) > 7*60):
                        # only after 7min into the roast and if CHARGE is marked
                        self.aw.qmc.autoDropIdx = len(self.aw.qmc.timex) - 2
                        self.aw.qmc.markDropSignal.emit(True) # DROP
    #                elif event_flag == 9 and self.aw.qmc.timeindex[0] > -1 and self.aw.qmc.timeindex[6] >= 0 and self.aw.qmc.timeindex[7] == 0:
    #                    self.aw.qmc.markCoolSignal.emit(True) # COOL
                except Exception as e: # pylint: disable=broad-except
                    _log.error(e)
        return tx,t2,t1 # time, ET (chan2), BT (chan1)



    def Kaleido_SVAT(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        if self.aw.kaleido is not None:
            t1,t2 = self.aw.kaleido.getSVAT()
            # if in Kaleido PID mode, we turn adjust the SV if TS data changes to sync with the machine state
            if self.aw.kaleidoPID:
                try:
                    ts = int(round(t1))
                    self.aw.setSVSignal.emit(ts)
                except Exception as e: # pylint: disable=broad-except
                    _log.error(e)
        else:
            t1 = t2 = -1
        return tx,t2,t1 # time, AT (chan2), SV (chan1)

    def Kaleido_DrumAH(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        if self.aw.kaleido is not None:
            t1,t2 = self.aw.kaleido.getDrumAH()
            # if in Kaleido PID mode, we turn ArtisanPID ON/OFF if AH signal changes to sync with the machine state
            if self.aw.kaleidoPID:
                try:
                    ah = bool(round(t2))
                    if ah and not self.aw.pidcontrol.pidActive:
                        # machine says its PID is on, we reflect this on the Artisan side
                        self.aw.pidOnSignal.emit()
                    elif not ah and self.aw.pidcontrol.pidActive:
                        # machine says its PID is off, we reflect this on the Artisan side
                        self.aw.pidOffSignal.emit()
                except Exception as e: # pylint: disable=broad-except
                    _log.error(e)
        else:
            t1 = t2 = -1
        return tx,t2,t1 # time), AH (chan2), Drum (chan1)

    def Kaleido_HeaterFan(self) -> tuple[float,float,float]:
        tx = self.aw.qmc.timeclock.elapsedMilli()
        if self.aw.kaleido is not None:
            t1,t2 = self.aw.kaleido.getHeaterFan()
        else:
            t1 = t2 = -1
        return tx,t2,t1 # time, Fan (chan2), Heater (chan1)

############################################################################
    def openport(self) -> None:
        try:
            #open port
            if not self.SP.is_open:
                self.confport()
                self.SP.open()
                libtime.sleep(.1) # avoid possible hickups on startup
                if self.aw.seriallogflag:
                    settings = str(self.comport) + ',' + str(self.baudrate) + ',' + str(self.bytesize)+ ',' + str(self.parity) + ',' + str(self.stopbits) + ',' + str(self.timeout)
                    self.aw.addserial('serial port opened: ' + settings)
        except Exception: # pylint: disable=broad-except
            self.SP.close()
            error = QApplication.translate('Error Message','Serial Exception:') + ' ' + QApplication.translate('Error Message','Unable to open serial port')
            self.aw.qmc.adderror(error)

    #loads configuration to ports
    def confport(self) -> None:
        self.SP.port = self.comport
        self.SP.baudrate = self.baudrate
        self.SP.bytesize = self.bytesize
        self.SP.parity = self.parity
        self.SP.stopbits = self.stopbits
        self.SP.timeout = self.timeout
        if self.platf != 'Windows':
            self.SP.exclusive = True

    def closeport(self) -> None:
        try:
            if self.SP.is_open:
                self.SP.close()
        except Exception: # pylint: disable=broad-except
            pass

    def NONEtmp(self) -> tuple[float, float]:
        dialogx = nonedevDlg(self.aw, self.aw)

        # NOT CORRECT:
        ##from sys import getsizeof  # getsizesof not reporting the full size here!
        ##print(getsizeof(dialogx)) # 192bytes using slots; 152bytes without slots;

        # # sudo -H python3 -m pip install pympler
        #from pympler import asizeof
        #print(asizeof.asizeof(dialogx)) # 2440 using slots; 2568 without using slots
        if dialogx.exec():
            try:
                ETraw = dialogx.etEdit.text().split('.')
                ET = (int(str(ETraw[0])) * 10)/10.
            except Exception: # pylint: disable=broad-except
                ET = -1
            try:
                BTraw = dialogx.btEdit.text().split('.')
                BT = (int(str(BTraw[0])) * 10)/10.
            except Exception as e: # pylint: disable=broad-except
                _log.exception(e)
                BT = -1
            try:
                dialogx.okButton.clicked.disconnect()
                dialogx.cancelButton.clicked.disconnect()
                QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
                try: # sip not supported on older PyQt versions (RPi!)
                    sip.delete(dialogx)
                    #print(sip.isdeleted(dialogx))
                except Exception: # pylint: disable=broad-except
                    pass
                del dialogx
            except Exception: # pylint: disable=broad-except
                pass
            return ET, BT
        try:
            dialogx.okButton.clicked.disconnect()
            dialogx.cancelButton.clicked.disconnect()
            QApplication.processEvents() # we ensure events concerning this dialog are processed before deletion
            try: # sip not supported on older PyQt versions (RPi!)
                sip.delete(dialogx)
                #print(sip.isdeleted(dialogx))
            except Exception: # pylint: disable=broad-except
                pass
            del dialogx
        except Exception: # pylint: disable=broad-except
            pass
        return -1, -1

    #sends a command to the ET/BT device. (used by eventaction to send serial command)
    def sendTXcommand(self, command:bytes|str) -> None:
        try:
            #### lock shared resources #####
            self.aw.qmc.samplingSemaphore.acquire(1)
            if not self.SP.is_open:
                self.openport()
            if self.SP.is_open:
                self.SP.reset_input_buffer()
                self.SP.reset_output_buffer()
                if isinstance(command, str):
                    self.SP.write(str2cmd(command))
                elif isinstance(command, bytes):
                    self.SP.write(command)
                #self.SP.flush()
        except Exception as ex:  # pylint: disable=broad-except
            _log.exception(ex)
            #self.closeport() # do not close the serial port as reopening might take too long
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror((QApplication.translate('Error Message','Exception:') + ' ser.sendTXcommand() {0}').format(str(ex)),getattr(exc_tb, 'tb_lineno', '?'))
        finally:
            if self.aw.qmc.samplingSemaphore.available() < 1:
                self.aw.qmc.samplingSemaphore.release(1)
            #note: logged chars should not be binary
            if self.aw.seriallogflag:
                settings = str(self.comport) + ',' + str(self.baudrate) + ',' + str(self.bytesize)+ ',' + str(self.parity) + ',' + str(self.stopbits) + ',' + str(self.timeout)
                self.aw.addserial(f'Serial Command: {settings} || Tx = {command!r} || Rx = No answer needed')



#########################################################################
#############  Extra Serial Ports #######################################
#########################################################################

class extraserialport:

    __slots__ = ['aw', 'comport', 'baudrate', 'bytesize', 'parity', 'stopbits', 'timeout', 'devicefunctionlist', 'device', 'SP']

    def __init__(self, aw:'ApplicationWindow') -> None:
        self.aw = aw

        #default initial settings. They are changed by settingsload() at initiation of program according to the device chosen
        self.comport:str = '/dev/cu.usbserial-FTFKDA5O'      #NOTE: this string should not be translated.
        self.baudrate:int = 19200
        self.bytesize:int = 8
        self.parity:str= 'N'
        self.stopbits:int = 1
        self.timeout:float = 0.4
        self.devicefunctionlist:dict[str, Callable[[], tuple[float,float,float]]|None] = {}
        self.device:str|None = None
        self.SP:serial.Serial|None = None

    def confport(self) -> None:
        if self.SP is not None:
            self.SP.port = self.comport
            self.SP.baudrate = self.baudrate
            self.SP.bytesize = self.bytesize
            self.SP.parity = self.parity
            self.SP.stopbits = self.stopbits
            self.SP.timeout = self.timeout
            if platform.system() != 'Windows':
                self.SP.exclusive = True

    def openport(self) -> None:
        try:
            self.confport()
            #open port
            if self.SP is not None and not self.SP.is_open:
                self.SP.open()
        except Exception:  # pylint: disable=broad-except
            if self.SP is not None:
                self.SP.close()
            error = QApplication.translate('Error Message','Serial Exception:')
            _, _, exc_tb = sys.exc_info()
            self.aw.qmc.adderror(error + ' Unable to open serial port',getattr(exc_tb, 'tb_lineno', '?'))

    def closeport(self) -> None:
        if self.SP is not None:
            self.SP.close()

    # this one is called from scale and color meter code
    def connect(self,error:bool=True) -> bool:
        if self.SP is None:
            try:
                import serial  # @UnusedImport
                self.SP = serial.Serial()
            except Exception as e:  # pylint: disable=broad-except
                if error:
                    _, _, exc_tb = sys.exc_info()
                    self.aw.qmc.adderror((QApplication.translate('Error Message','Serial Exception:') + ' connect() {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))
        if self.SP is not None:
            try:
                self.openport()
                return bool(self.SP.is_open)
            except Exception as e:  # pylint: disable=broad-except
                if error:
                    _, _, exc_tb = sys.exc_info()
                    self.aw.qmc.adderror((QApplication.translate('Error Message','Serial Exception:') + ' connect() {0}').format(str(e)),getattr(exc_tb, 'tb_lineno', '?'))
                return False
        else:
            return False
