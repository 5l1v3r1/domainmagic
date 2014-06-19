import thread
from dns import resolver
from tasker import ThreadPool,Task,TaskGroup
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
        #todo: type
        results.append(dnr)
     
    return results


class DNSLookup(object):
    def __init__(self):
        self.resolver=resolver.Resolver()
        self.threadpool=ThreadPool(10)
        
    
    def lookup(self,question,qtype='A'):
        """lookup one record returns a list of DNSLookupResult"""
        resolveranswer = self.resolver.query(question, qtype)
        results=_make_results(question,qtype,resolveranswer)
        return results
    
    def lookup_multi(self,questions, qtype='A'):
        """lookup a list of multiple records of the same qtype. the lookups will be done in parallel"""
        
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
        
        while result==None:
            pass
            
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
    
    
    