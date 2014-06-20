import thread
from dns import resolver
from dns.rdatatype import to_text as rdatatype_to_text
 
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
        dnr.rtype=rdatatype_to_text(resolveranswer.rdtype)
        results.append(dnr)
     
    return results


class DNSLookup(object):
    threadpool=ThreadPool(10)
    
    def __init__(self):    
        self.nameservers=None
        #override here
        self.nameservers=['91.208.173.38',]
        
        #TODO: timeout/override ns doesn't seem to work yet
        
        self.timeout=3
        
        self.resolver=resolver.Resolver()
        
        self.logger=logging.getLogger("dnslookup")
        
    def lookup(self,question,qtype='A'):
        """lookup one record returns a list of DNSLookupResult"""
        resolveranswer=None
        try:
            resolveranswer = self.resolver.query(question, qtype)
        except resolver.NXDOMAIN:
            pass
        except Exception,e:
            self.logger.warning("dnslookup %s/%s failed: %s"%(question,qtype,str(e)))
            
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
        
        while result==None:
            pass
        
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
    
    
    