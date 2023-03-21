#!/usr/bin/env python3

import os
import sys
import subprocess
import signal
from dicomlistner import Dicomservice

import socket

settings = {}
params = dict()
log = ""
basedir = ""

if sys.platform == 'win32':
    import win32serviceutil
    import servicemanager
    import win32event
    import win32service
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    params['startupinfo'] = startupinfo
    class InvesaliusService(win32serviceutil.ServiceFramework):
        _svc_name_ = "InvesaliusService"
        _svc_display_name_ = "Invesalius Pusher Service"
        _svc_description_ = "Dicom Receiver"
        def __init__(self,args):
            win32serviceutil.ServiceFramework.__init__(self, *args)
            self.log('Service Initialized.')
            # Create an event which we will use to wait on.
            # The "service stop" request will set this event.
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.dicom = Dicomservice(basedir)
            socket.setdefaulttimeout(60)


        def log(self, msg):
            servicemanager.LogInfoMsg(str(msg))

        def sleep(self, sec):
            win32api.Sleep(sec*1000, True)

        def SvcStop(self):
            # tell the SCM we are starting the stop process.
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.stop()
            self.log('Service has stopped.')
            # And set stop  event.
            win32event.SetEvent(self.stop_event)
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)

        def SvcDoRun(self):
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            try:
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
                self.log('Service is starting.')
                self.main()
                win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
                servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))
            except Exception as e:
                s = str(e)
                self.log('Exception :'+s)
                self.SvcStop()

        def stop(self):
            self.runflag=False
            try:
                self.dicom.stop()
            except Exception as e:
                self.log(str(e))

        def main(self):
            self.runflag=True
            self.dicom.start()
            while self.runflag:
                rc = win32event.WaitForSingleObject(self.stop_event, 24*60*60)
                # Check to see if self.hWaitStop happened
                if rc == win32event.WAIT_OBJECT_0:
                    self.log("Service has stopped")
                    break
                else:
                    try:
                        pass
                    except Exception as e:
                        self.log(str(e))

    if __name__ == '__main__':
        basedir = os.path.dirname(os.path.realpath(__file__))+"/"
        #tbd need to replace hardcoded value of directory with windows registry
        basedir = "C:/dcmrecevier/"
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(InvesaliusService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(InvesaliusService)
else:


    if __name__ == "__main__":
        basedir = os.path.dirname(os.path.realpath(__file__))+"/"
        dicom = Dicomservice(basedir)
        dicom.start()
