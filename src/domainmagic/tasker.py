import threading
import time
import Queue
import logging

class Task(object):
    def __init__(self,method,args=None,kwargs=None,callback=None):
        self.method=method
        if args!=None:
            self.args=args
        else:
            self.args=()
            
        if kwargs!=None:
            self.kwargs=kwargs
        else:
            self.kwargs={}
        self.callback=callback        
        self.done=False
        self.result=None
        
        
    def execute(self,worker):
        self.result=self.method(*self.args,**self.kwargs)
        self.done=True
        
        if self.callback!=None:
            self.callback(self)
            
            
class TaskGroup(object):
    def __init__(self,progresscallback=None,completecallback=None):
        self.tasks=[]
        self.progresscallback=progresscallback
        self.completecallback=completecallback
        
    def add_task(self,method,args=None,kwargs=None):
        """add a method call to the task group. and return the task object."""
        t=Task(method,args=args,kwargs=kwargs,callback=self._task_done)
        self.tasks.append(t)
        return t
    
    def _task_done(self,task):
        if self.progresscallback!=None:
            self.progresscallback(self,task)
        
        if self.completecallback!=None:
            for task in self.tasks:
                if not task.done:
                    return
            self.done=True
            self.completecallback(self)
        
    def execute(self,worker):
        for task in self.tasks:
            worker.pool.add_task(task)      
        
        
class ThreadPool(threading.Thread):
    
    def __init__(self,minthreads=1,maxthreads=None,queuesize=100):
        self.workers=[]
        self.queuesize=queuesize
        self.tasks=Queue.Queue(queuesize)
        self.minthreads=minthreads
        
        if maxthreads==None:
            maxthreads=9999
        
        self.maxthreads=maxthreads
        assert self.minthreads>0
        assert self.maxthreads>self.minthreads
        
        self.logger=logging.getLogger('threadpool')
        self.threadlistlock=threading.Lock()
        self.checkinterval=10
        self.threadcounter=0
        self.stayalive=True
        self.laststats=0
        self.statinverval=60
        threading.Thread.__init__(self)
        self.setDaemon(False)
        self.start()
        

    def add_task(self,task):
        self.tasks.put(task)
    
    def get_task(self):
        try:
            task=self.tasks.get(True, 1)
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
            if changed or time.time()-self.laststats>self.statinverval:
                workerlist="\n%s"%'\n'.join(map(repr,self.workers))
                self.logger.debug('queuesize=%s workload=%.2f workers=%s workerlist=%s'%(queuesize,workload,numthreads,workerlist))
                self.laststats=time.time()
                
            time.sleep(self.checkinterval)
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
    

class Worker(threading.Thread):
    def __init__(self,workerid,pool):
        threading.Thread.__init__(self)
        self.workerid=workerid
        self.birth=time.time()
        self.pool=pool
        self.stayalive=True
        self.logger=logging.getLogger('worker.%s'%workerid)
        self.logger.debug('thread init')
        self.noisy=False
        self.setDaemon(False)
        self.threadinfo='created'
    
    def __repr__(self):
        return "%s: %s"%(self.workerid,self.threadinfo)
       
    def run(self):
        while self.stayalive:
            time.sleep(0.1)
            self.threadinfo='waiting for task'
            task=self.pool.get_task()
            if task==None:
                continue
            try:
                task.execute(self)
            except Exception,e:
                self.logger.error('Unhandled Exception : %s'%e)
            self.threadinfo='task completed'
        
        self.threadinfo='ending'

        

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    def dummy():
        import random
        rand=random.randint(1,10)
        time.sleep(rand)
        return rand
    
    def progress(taskgroup,task):
        print "Task got result : %s"%(task.result)
    
    def complete(taskgroup):
        print "Taskgroup complete"    
    
    t=ThreadPool(50)
    
    
    #for i in range(0,50):
    #    print "adding task %s"%i
    #    t.add_task(Task(dummy,callback=printresult))
    #print "done adding tasks"
    
    tg=TaskGroup(progress, complete)
    for i in range(0,50):
        tg.add_task(dummy)
    print "taskgroup created"
    t.add_task(tg)
    
    try:
        raw_input()
    except:
        pass
    
    t.stayalive=False
        