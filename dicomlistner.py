#!/usr/bin/env python3
"""A Storage SCP application.

Used for receiving DICOM SOP Instances transferred from an SCU.
"""

import os
import sys
import threading
import glob
import tempfile
import zipfile
import subprocess
import time
import logging
import paramiko
from logging.handlers import RotatingFileHandler
from pathlib import Path
import shutil
import json
import signal
from pydicom.dataset import Dataset
from pydicom.uid import (
    ExplicitVRLittleEndian, ImplicitVRLittleEndian, ExplicitVRBigEndian
)

from pynetdicom import (
    AE, evt,debug_logger,
    AllStoragePresentationContexts,
    VerificationPresentationContexts,
    debug_logger,
    StoragePresentationContexts,
)
from pynetdicom._globals import ALL_TRANSFER_SYNTAXES, DEFAULT_MAX_LENGTH
from pydicom.filewriter import write_file_meta_info
from pydicom import dcmread
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelMove,StudyRootQueryRetrieveInformationModelMove,PatientStudyOnlyQueryRetrieveInformationModelMove
import socket

settings = {}
params = dict()
log = ""
basedir = "./"
class Dicomservice():
#Calback function which is called on receiving a dicom image
    def storehandle(self,event):
        ds = event.dataset
        date = ds.StudyDate
        time = ds.StudyTime
        modality = ds.Modality
        print(event.assoc.requestor.primitive.calling_ae_title)
        targetdir = self.basedir + "/dcmdata/" + ds.StudyInstanceUID
        if not os.path.exists(targetdir):
            os.makedirs(targetdir)
        targetdir = targetdir + "/" + ds.SeriesInstanceUID
        if not os.path.exists(targetdir):
            os.makedirs(targetdir)
        filename = '%s/%s.dcm' % (targetdir, ds.SOPInstanceUID)
        if  os.path.exists(filename):
            return 0x0000
        with open(filename, 'wb') as dcmfile:
            dcmfile.write(b'\x00' * 128)
            dcmfile.write(b'DICM')
            write_file_meta_info(dcmfile, event.file_meta)
            dcmfile.write(event.request.DataSet.getvalue())
        return 0x0000


    def handle_open(self,event):
        msg = 'Request from host ip and port remote at {}'.format(event.address)
        logging.info(msg)
    def start(self):
        port = settings["PORT"].replace('"', '')
        port = int(port)
        handlers = [ (evt.EVT_CONN_OPEN, self.handle_open),(evt.EVT_C_STORE, self.storehandle)]
        self.ae.start_server(("", port), evt_handlers=handlers)
    

    def stop(self):
        self.ae.shutdown()
        self.thread.cancel()

    #settings and dicom listener initialising  function
    def  __init__(self,newdir):
        """Run the application."""
        basedir = newdir
        self.basedir =  basedir+"/"
        with open(self.basedir+"/settings.txt","r") as f:
            lines = (line.rstrip() for line in f)
            lines = (line for line in lines if line)
            for line in lines:
                name, value = line.split("=")
                settings[name.strip()] = value.strip()
        LOG_FILENAME = self.basedir+'/log.txt'
        logging.basicConfig(filename=LOG_FILENAME,format='%(asctime)s - %(message)s',level=logging.INFO,)
        handler = RotatingFileHandler(LOG_FILENAME, mode='a', maxBytes=5*1024*1024,backupCount=2, encoding=None, delay=0)
        """ enable debug_logger by uncommenting if you want to see all dicom messages """
        #debug_logger()
        log = logging.getLogger('pynetdicom')
        log.addHandler(handler)

 
    
        # Set Transfer Syntax options
        transfer_syntax = ALL_TRANSFER_SYNTAXES[:]
    
    
        # Create application entity
        ae_title = settings["AETITLE"].replace('"', '')
        ae = AE(ae_title=ae_title)
    
        # Add presentation contexts with specified transfer syntaxes
        for context in AllStoragePresentationContexts:
            ae.add_supported_context(context.abstract_syntax, transfer_syntax)
    
        for context in VerificationPresentationContexts:
            ae.add_supported_context(context.abstract_syntax, transfer_syntax)
        
        self.ae = ae
         
  
if __name__ == "__main__":
    basedir = os.path.dirname(os.path.realpath(__file__))+"/"
    dicom = Dicomservice(basedir)
    dicom.start()
