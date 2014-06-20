import logging
import threading
import time
import os
import tempfile
import urllib2
import thread
import zlib

class FileTooSmallException(Exception):
    pass



class FileUpdater(object):
    def __init__(self):
        #key: local absolute path
        #value: dict:
        # - update_url
        # - refresh_time
        # - minimum_size
        # - lock (threading.Lock object, created by add_file)
        self.defaults={
         'refresh_time':86400,
         'minimum_size':0,        
        }
        self.filedict={}
        self.logger=logging.getLogger('fileupdater')
    
    def add_file(self,local_path,update_url,refresh_time=None,minimum_size=None,unpack=False):
        valdict=dict()
        valdict['refresh_time']=refresh_time or self.defaults['refresh_time']
        valdict['minimum_size']=minimum_size or self.defaults['minimum_size']
        valdict['unpack']=unpack
        valdict['lock']=threading.Lock()
        valdict['update_url']=update_url
        
        self.filedict[local_path]=valdict
        self.update_in_thread(local_path)

    
    def file_modtime(self,local_path):
        """returns the file modification timestamp"""
        statinfo=os.stat(local_path)
        return max(statinfo.st_ctime,statinfo.st_mtime)
    
    def file_age(self,local_path):
        """return the file age in seconds"""
        return time.time()-self.file_modtime(local_path)
    
    def is_recent(self,local_path):
        """returns True if the file mod time is within the configured refresh_time"""
        if not os.path.exists(local_path):
            return False
        
        return self.file_age(local_path)<self.filedict[local_path]['refresh_time']
    
    def update(self,local_path,force=False):
        #if the file is current, do not update
        if self.is_recent(local_path) and not force:
            self.logger.debug("File %s is current - not updating"%local_path)
            return
        
        self.logger.debug("Updating %s - aquire lock"%local_path)
        self.filedict[local_path]['lock'].acquire()
        
        
        #check again in case we were waiting for the lock before and some other thread just updated the file
        if self.is_recent(local_path) and not force:
            self.logger.debug("File %s is current - not updating"%local_path)
            return
        
        try:
            #TODO: we could optimize here, if-modified-since for example
            update_url=self.filedict[local_path]['update_url']
            response = urllib2.urlopen(update_url)
            content = response.read()
            content_len=len(content)
            self.logger.debug("%s bytes downloaded from %s"%(content_len,update_url))
            handle,tmpfilename=tempfile.mkstemp()
            if len(content)<self.filedict[local_path]['minimum_size']:
                raise FileTooSmallException("file size %s downloaded from %s is smaller than configured minimum of %s bytes"%(content_len, update_url,self.filedict[local_path]['minimum_size']))                


            #TODO: add zip etc here
            #http://stackoverflow.com/questions/3122145/zlib-error-error-3-while-decompressing-incorrect-header-check
            if self.filedict[local_path]['unpack']==True:
                if update_url.lower().endswith('.gz'): #TODO: we'd probably have to really parse the update url, this would fail with url arguments atm
                    content=zlib.decompress(content,zlib.MAX_WBITS | 16)
            
            fd=os.fdopen(handle,'w')
            fd.write(content)
            fd.close()
            
    
            
            
            os.rename(tmpfilename, local_path)
            
        finally:
            self.filedict[local_path]['lock'].release()
            self.logger.debug("%s - lock released"%local_path)
            
        
    def update_in_thread(self,local_path,force=False):
        thread.start_new_thread(self.update, (local_path,force),)
    
    def wait_for_file(self,local_path,force_recent=False):
        """make sure file :localpath exists locally.
        if it doesn't exist, it will be downloaded immediately and this call will block
        if it exists and force_recent is false, the call will immediately return
        if force_recent is true the age of the file is checked und the file will be re-downloaded in case it's too old"""
        
        if local_path not in self.filedict:
            raise ValueError("File not configured for auto-updating - please call add_file first!")
        
        if os.path.exists(local_path):
            if self.is_recent(local_path):
                return
            else:
                if force_recent:
                    self.update(local_path)
                else:
                    self.update_in_thread(local_path)
        else:
            self.update(local_path)
        

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    updater=FileUpdater()
    updater.add_file("/tmp/tldalpha.txt", "http://data.iana.org/TLD/tlds-alpha-by-domain.txt", 10, 1000)
    updater.wait_for_file("/tmp/tldalpha.txt", True)
    
