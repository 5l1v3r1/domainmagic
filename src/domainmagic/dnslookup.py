import thread
import threading
from dns import resolver
from dns.rdatatype import to_text as rdatatype_to_text
 
from tasker import get_default_threadpool,Task,TaskGroup
import time
import logging

class DNSLookupResult(object):
    def __init__(self):
        self.qtype=None
        self.question=None
        self.name=None
        self.content=None
        self.ttl=None
        self.rtype=None
        
    
    def __str__(self):
        return str(self.content)

    def __repr__(self):
        return "<type='%s' content='%s' ttl='%s'>"%(self.rtype,self.content,self.ttl)
    
    def __unicode__(self):
        return str(self.content)
    

def _make_results(question,qtype,resolveranswer):
    results=[]
    for answer in resolveranswer:
        dnr=DNSLookupResult()
        dnr.question=question
        dnr.qtype=qtype
        dnr.content=answer.to_text()
        dnr.ttl=resolveranswer.rrset.ttl
        dnr.rtype=rdatatype_to_text(resolveranswer.rdtype)
        results.append(dnr)
     
    return results


class DNSLookup(object):
    threadpool=get_default_threadpool()
    
    MAX_PARALLEL_REQUESTS=10
    
    semaphore=threading.Semaphore(MAX_PARALLEL_REQUESTS)
    
    def __init__(self):    
        self.nameservers=None
        #override here
        self.nameservers=['91.208.173.38',]    
        
        if self.nameservers==None:
            self.resolver=resolver.Resolver()
        else:
            self.resolver=resolver.Resolver(configure=False)
            self.resolver.nameservers=self.nameservers
            #print self.resolver.nameservers
        
        
        self.resolver.timeout = 3   # timeout for a individual request before retrying
        self.resolver.lifetime = 10 # max time for a request 
        self.multitimeout=10
        
        
        
        self.logger=logging.getLogger("dnslookup")
        
    def lookup(self,question,qtype='A'):
        """lookup one record returns a list of DNSLookupResult"""
        assert type(question)==str
        
        resolveranswer=None
        
        try:
            DNSLookup.semaphore.acquire(False)
            self.logger.debug("query: %s/%s"%(question,qtype))
            resolveranswer = self.resolver.query(question, qtype)
            self.logger.debug("query %s/%s completed -> %s"%(question,qtype,resolveranswer))
        except resolver.NXDOMAIN:
            pass
        except Exception,e:
            #TODO: some dnspython exceptions don't have a description - maybe add the full stack?
            self.logger.warning("dnslookup %s/%s failed: %s"%(question,qtype,str(e)))
        finally:
            DNSLookup.semaphore.release()
            
            
        if resolveranswer!=None:
            results=_make_results(question,qtype,resolveranswer)
            return results
        else:
            return []
        
    
    def lookup_multi(self,questions, qtype='A'):
        """lookup a list of multiple records of the same qtype. the lookups will be done in parallel
        returns a dict question->[list of DNSLookupResult]
        """
        
        global result
        result=None
        def _waitforresult(taskgroup):
            global result
            tempresult={}
            for task in taskgroup.tasks:
                assert task.done
                tempresult[task.args[0]]=task.result
            result=tempresult
            
        
        tg=TaskGroup(completecallback=_waitforresult)
        for question in questions:
            tg.add_task(self.lookup,args=(question,qtype))
        
        self.threadpool.add_task(tg)
        
        starttime=time.time()
        while result==None:
            if time.time()-starttime>self.multitimeout:
                self.logger.warn('timeout in lookup_multi')
                tempresult={}
                compcounter=0
                for task in tg.tasks:
                    if task.done:
                        tempresult[task.args[0]]=task.result
                        compcounter+=1
                    else:
                        self.logger.warn( "hanging lookup: %s"%task)
                self.logger.warn("%s of %s tasks completed"%(compcounter,len(tg.tasks)))
                result=tempresult
                
        
        #print "lookup multi, questions=%s, qtype=%s , result=%s"%(questions,qtype,result)
        
        return result
        
        
        
         
         
     
     
if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    d=DNSLookup()
    #print "Sync lookup:"
    #print d.lookup_sync('wgwh.ch')
    
    
    print "lookup start"
    start=time.time()
    result=d.lookup_multi(['wgwh.ch','heise.de','slashdot.org'])
    end=time.time()
    diff=end-start
    print "lookup end, time=%.4f"%diff
    print result
    
    
    