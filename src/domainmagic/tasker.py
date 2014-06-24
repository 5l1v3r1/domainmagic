import threading
import time
import Queue
import logging
import traceback

class Task(object):
    """Default task object used by the threadpool
    """
    def __init__(self,method,args=None,kwargs=None):
        self.method=method
        
        if args!=None:
            self.args=args
        else:
            self.args=()
            
        if kwargs!=None:
            self.kwargs=kwargs
        else:
            self.kwargs={}
                
        self.done=False
        """will be set to true after the task has been executed"""
        
        self.result=None
        """contains the result of the method call after the task has been executed"""
        
    def execute(self,worker):
        self.result=self.method(*self.args,**self.kwargs)
        self.done=True

    def __repr__(self):
        return "<Task method='%s' args='%s' kwargs='%s' done=%s >"%(self.method,self.args,self.kwargs, self.done)
        
class TimeOut(Exception):
    pass
      
class TaskGroup(object):
    """Similar to Task, but can be used to run multiple methods in parallel
    """
    
    def __init__(self):
        self.tasks=[]
        
    def add_task(self,method,args=None,kwargs=None):
        """add a method call to the task group. and return the task object.
        the resulting task object should *not* be modified by the caller
        and should not be added to a threadpool again, this will be done automatically when the taskgroup is added to the threadpool
        """
        t=Task(method,args=args,kwargs=kwargs)
        self.tasks.append(t)
        return t
        
    def execute(self,worker):
        """add all tasks to the thread pool"""
        for task in self.tasks:
            worker.pool.add_task(task)
    
    def join(self,timeout=None):
        """block until all tasks in this group are done"""
        starttime=time.time()
        while True:
            if timeout!=None:
                if time.time()-starttime>timeout:
                    raise TimeOut()
                    
            if self.all_done():
                return
            time.sleep(0.01)
            
    
    def all_done(self):
        for task in self.tasks:
            if not task.done:
                return False
        return True
        
global default_threadpool
default_threadpool=None

def get_default_threadpool():
    global default_threadpool
    if default_threadpool==None:
        default_threadpool=ThreadPool(minthreads=20,maxthreads=100,queuesize=100)
    return default_threadpool


  
class ThreadPool(threading.Thread):
    
    def __init__(self,minthreads=1,maxthreads=None,queuesize=100):
        """Initialize and start the threadpool. if maxthreads is None a default of minthreads+20 will be used"""
        
        self.mainthread=threading.current_thread()
        
        self.workers=[]
        self.queuesize=queuesize
        self.tasks=Queue.Queue(queuesize)
        self.minthreads=minthreads
        
        if maxthreads==None:
            maxthreads=minthreads+20
        
        self.maxthreads=maxthreads
        assert self.minthreads>0
        assert self.maxthreads>self.minthreads
        
        self.logger=logging.getLogger('threadpool')
        self.threadlistlock=threading.Lock()
        self.checkinterval=3
        self.threadcounter=0
        self.stayalive=True
        self.laststats=0
        self.statinverval=60
        threading.Thread.__init__(self)
        self.setDaemon(False)
        self.start()
        

    def add_task(self,task):
        """Add task or taskgroup to the queue. You may also add custom task objects, as long as they have a .execute(worker) method
        this will block if the queue is full
        """
        self.tasks.put(task)
    
    def get_task(self,timeout=2):
        """get the next task from the queue. returns None if there is no task at the moment"""
        try:
            task=self.tasks.get(True, timeout)
            return task
        except Queue.Empty:
            return None
        
         
    
    def run(self):
        self.logger.debug('Threadpool initialising. minthreads=%s maxthreads=%s maxqueue=%s checkinterval=%s'%(self.minthreads,self.maxthreads,self.queuesize,self.checkinterval) )
        
        
        while self.stayalive:
            curthreads=self.workers
            numthreads=len(curthreads)
            
            #check the minimum boundary
            requiredminthreads=self.minthreads
            if numthreads<requiredminthreads:
                diff=requiredminthreads-numthreads
                self._add_worker(diff)
                continue
            
            #check the maximum boundary
            if numthreads>self.maxthreads:
                diff=numthreads-self.maxthreads
                self._remove_worker(diff)
                continue
            
            changed=False
            #ok, we are within the boundaries, now check if we can dynamically adapt something
            queuesize=self.tasks.qsize()
            
            #if there are more tasks than current number of threads, we try to increase
            workload=float(queuesize)/float(numthreads)
            
            if workload>1 and numthreads<self.maxthreads:
                self._add_worker()
                numthreads+=1
                changed=True
                
            
            if workload<1 and numthreads>self.minthreads:
                self._remove_worker()
                numthreads-=1
                changed=True
            
            #log current stats
            #if changed or time.time()-self.laststats>self.statinverval:
            #    workerlist="\n%s"%'\n'.join(map(repr,self.workers))
            #    self.logger.debug('queuesize=%s workload=%.2f workers=%s workerlist=%s'%(queuesize,workload,numthreads,workerlist))
            #    self.laststats=time.time()
            
            time.sleep(self.checkinterval)
            #if main thread exits we shutdown too
            if not self.mainthread.is_alive():
                self.logger.debug("Main thread shut down -> shutting down threadpool")
                self.stayalive=False
            
        for worker in self.workers:
            worker.stayalive=False
        del self.workers
        self.logger.info('Threadpool shut down')
    
    
    def _remove_worker(self,num=1):
        self.logger.debug('Removing %s workerthread(s)'%num)
        for bla in range(0,num):
            worker=self.workers[0]
            worker.stayalive=False
            del self.workers[0]
        
    
    def _add_worker(self,num=1):
        self.logger.debug('Adding %s workerthread(s)'%num)
        for bla in range(0,num):
            self.threadcounter+=1
            worker=Worker("[%s]"%self.threadcounter,self)
            self.workers.append(worker)
            worker.start()
            
    def shutdown(self):
        self.stayalive=False
    

class Worker(threading.Thread):
    def __init__(self,workerid,pool):
        threading.Thread.__init__(self)
        self.workerid=workerid
        self.birth=time.time()
        self.pool=pool
        self.stayalive=True
        self.logger=logging.getLogger('worker.%s'%workerid)
        self.noisy=False
        self.setDaemon(False)
        self.threadinfo='created'
    
    def __repr__(self):
        return "%s: %s"%(self.workerid,self.threadinfo)
       
    def run(self):
        while self.stayalive:
            self.threadinfo='waiting for task'
            task=self.pool.get_task()
            if task==None:
                continue
            try:
                self.threadinfo="executing task %s"%task
                task.execute(self)
            except Exception,e:
                self.logger.error('Unhandled Exception in workertask %s : %s'%(str(self),str(e)))
                self.logger.error(traceback.format_exc())
            self.threadinfo='task completed'
        
        self.threadinfo='ending'

        
