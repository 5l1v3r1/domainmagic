import thread
from dns import resolver

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
    
    def lookup_sync(self,question,qtype='A'):
        """returns a list of DNSLookupResult"""
        resolveranswer = self.resolver.query(question, qtype)
        results=_make_results(question,qtype,resolveranswer)
        return results
    
    def _lookup_in_thread(self,question,callback, callbackarg,qtype='A'):
        ret=lookup(question,qtype=qtype)
        callback(ret,callbackarg)
        
    
    def lookup_async(self,question,callback, callbackarg, qtype='A'):
         #TODO: for now we use a simple thread -> convert to threadpool later
         thread.start_new(self._lookup_in_thread, (question,callback, callbackarg, qtype),)
     
     
if __name__=='__main__':
    d=DNSLookup()
    print d.lookup_sync('wgwh.ch')
    
    
    