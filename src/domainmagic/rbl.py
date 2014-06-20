from tasker import *
import logging
from dnslookup import DNSLookup
from ip import ip_reversed
from validators import is_ip
import re
from string import Template
import os


def remove_trailing_dot(input):
    """if input ends with a dot, remove it"""
    if input.endswith('.'):
        return input[:-1]
    else:
        return input

def add_trailing_dot(input):
    if not input.endswith('.'):
        return input+'.'
    else:
        return input

class RBLProviderBase(object):
    """Baseclass for all rbl providers"""
    
    def __init__(self,rbldomain):
        self.replycodes={}
        self.rbldomain=rbldomain
        self.logger=logging.getLogger('cmbl.rbllookup.%s'%self.rbldomain)
        self.resolver=DNSLookup()
        self.descriptiontemplate="${input} is listed on ${rbldomain} (${identifier})"

    def add_replycode(self,mask,identifier=None):
        """add a replycode/bitmask. identifier is any object which will be returned if a dns result matches this replycode
        if identifier is not passed, the lookup domain will be used"""
        
        if identifier==None:
            identifier=self.rbldomain
        
        self.replycodes[mask]=identifier
    
    def _listed_identifiers(self,input,transform,dnsresult):
        listings=[]
        for code,identifier in self.replycodes.items():
            if dnsresult == code:
                listings.append((code,self.make_description(input=input,dnsresult=dnsresult,transform=transform,identifier=identifier,replycode=code)))
        return listings

    def make_description(self,**values):
        """create a human readable listing explanation"""
        template=Template(self.descriptiontemplate)
        values['rbldomain']=self.rbldomain
        return template.safe_substitute(values)
    
    def transform_input(self,value):
        """transform input, eg, make md5 hashes here or whatever is needed for your specific provider"""
        return [value,]

    def make_lookup(self,transform):
        """some bls require additional modifications, even after input transformation, eg. ips must be reversed...
        by default we just remove trailing dots
        """
        return add_trailing_dot(transform)+self.rbldomain

    def listed(self,input):
        listings=[]
        transforms=self.transform_input(input)
        
        lookup_to_trans={}
        for transform in transforms:
            lookup_to_trans[self.make_lookup(transform)]=transform
        
        logging.debug( "lookup_to_trans=%s"%lookup_to_trans)
        
        
        multidnsresult=self.resolver.lookup_multi(lookup_to_trans.keys())
        
        for lookup,arecordlist in multidnsresult.iteritems():
            if lookup not in lookup_to_trans:
                self.logger.error("dns error: I asked for %s but got '%s' ?!"%(lookup_to_trans.keys(),lookup))
                continue
            
            for ipresult in arecordlist:
                listings.extend(self._listed_identifiers(input,lookup_to_trans[lookup],ipresult.content))

        return listings

    def __str__(self):
        return "<%s d=%s codes=%s>"%(self.__class__.__name__,self.rbldomain,self.replycodes)
    
    def __repr__(self):
        return str(self)

class BitmaskedRBLProvider(RBLProviderBase):                
    def _listed_identifiers(self,input,transform,dnsresult):
        """returns a list of identifiers matching the dns result"""
        listings=[]
        lastoctet=dnsresult.split('.')[-1]
        for mask,identifier in self.replycodes.items():
            if int(lastoctet) & mask == mask:
                desc=self.make_description(input=input,transform=transform,dnsresult=dnsresult,identifier=identifier,replycode=mask)
                listings.append((identifier,desc),)
        return listings

class ReverseIPMixin():
    """Direct lookups on IP Blacklists"""
    
    def make_lookup(self,transform):
        if is_ip(transform):
            return ip_reversed(transform)+'.'+self.rbldomain
        else:
            return add_trailing_dot(transform)+self.rbldomain
     
class StandardURIBLProvider(BitmaskedRBLProvider,ReverseIPMixin):
    """This is the most commonly used rbl provider (uribl, surbl)
     - domains are A record lookups example.com.rbldomain.com 
     - results are bitmasked  
     - ip lookups are reversed
    """
    pass

class BlackNSNameProvider(StandardURIBLProvider):
    """Nameserver Name Blacklists"""
    def __init__(self,rbldomain):
        StandardURIBLProvider.__init__(self, rbldomain)
        self.descriptiontemplate="${input}'s NS name ${transform} is listed on ${rbldomain} (${identifier})"
        
    def transform_input(self,value):
        ret=[]
        try:
            nsrecords=self.resolver.lookup(value,'NS')
            nsnames=[record.content for record in nsrecords]
            return nsnames
        except Exception,e:
            self.logger.warn("Exception in getting ns names: %s"%str(e))
        
        return ret

class BlackNSIPProvider(StandardURIBLProvider):
    """Nameserver IP Blacklists"""
    def __init__(self,rbldomain):
        StandardURIBLProvider.__init__(self, rbldomain)
        self.descriptiontemplate="${input}'s NSIP ${transform} is listed on ${rbldomain} (${identifier})"
    
    def transform_input(self,value):
        """transform input, eg, make md5 hashes here or whatever is needed for your specific provider"""
        ret=[]
        try:
            nsnamerecords=self.resolver.lookup(value,'NS')
            nsnames=[record.content for record in nsnamerecords]
            nsiprecords=self.resolver.lookup_multi(nsnames,'A').values()
            nsips=[]
            for recordlist in nsiprecords:
                nsips.extend([record.content for record in recordlist])
            return set(nsips)
        except Exception,e:
            self.logger.warn("Exception in black ns ip lookup: %s"%str(e))
        
        return ret

    def make_lookup(self,transform):
        return ip_reversed(transform)+'.'+self.rbldomain


class BlackAProvider(StandardURIBLProvider):
    """A record blacklists"""
    def __init__(self,rbldomain):
        StandardURIBLProvider.__init__(self, rbldomain)
        self.descriptiontemplate="${input}'s A record ${transform} is listed on ${rbldomain} (${identifier})"
    
    def transform_input(self,value):
        try:
            arecords=self.resolver.lookup(value,'A')
            ips=[record.content for record in arecords]
            return ips
        except Exception,e:
            self.logger.warn("Exception on a record lookup: %s"%str(e))
        
        return []

class FixedResultURIBLProvider(RBLProviderBase):
    """uribl lookups with fixed return codes, like the spamhaus DBL"""
    pass


class RBLLookup(object):
    def __init__(self):
        self.logger=logging.getLogger('cmbl.rbllookup')
        self.providers=[]
        
        self.providermap={
            'domain-bitmask':StandardURIBLProvider,
            'domain-fixed':FixedResultURIBLProvider,
            'nsip-bitmask':BlackNSIPProvider,
            'nsname-bitmask':BlackNSNameProvider,
            'a-bitmask':BlackAProvider,
        }
        #TODO: if we ever encounter fixed result rbls for ns/a we extend den from RBLProviderBase and 
        #move the current ones to use ReverseIPMixin
   
        
    def from_config(self,filepath=None):
        self.logger.debug('loading rbl lookups from file %s'%filepath)
        if not os.path.exists(filepath):
            self.logger.error("File not found: %s"%filepath)
        
        providers=[]
        
        for line in open(filepath).readlines():
            line=line.strip()
            if line=='' or line.startswith('#'):
                continue
            
            parts=line.split(None,2)
            if len(parts)!=3:
                self.logger.error("invalid config line: %s"%line)
                continue
            
            providertype,searchdomain,resultconfig=parts
            if providertype not in self.providermap:
                self.logger.error("unknown provider type %s"%(providertype))
                continue
            
            providerclass=self.providermap[providertype]
            
            providerinstance=providerclass(searchdomain)

            #set bitmasks
            for res in resultconfig.split():
                if ':' in res:
                    code,identifier=res.split(':',1)
                    try:
                        code=int(code)
                    except:
                        #fixed value
                        pass
                else:
                    identifier=res
                    code=2
                
                providerinstance.add_replycode(code,identifier)
            providers.append(providerinstance)
        self.providers=providers
        self.logger.debug("Providerlist from configfile: %s"%providers)
    
    def lookup(self,query):
        listed={}
        
        
        tg=TaskGroup()
        for provider in self.providers:
            tg.add_task(provider.listed, (query,), )
        get_default_threadpool().add_task(tg)
        tg.join(10)

        for task in tg.tasks:
            if task.done:
                for identifier,humanreadable in task.result:
                    listed[identifier]=humanreadable
        
        return listed.copy()



    
if __name__=='__main__':
    #logging.basicConfig(level=logging.DEBUG)
    rbl=RBLLookup()
    rbl.from_config('/home/gryphius/rbllookup.conf')
    
    import sys
    if len(sys.argv)<2:
        print "usage: rbl <something> [-debug]"
        sys.exit(1)
    
    if '-debug' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
    
    query=sys.argv[1]
    
    start=time.time()
    ans=rbl.lookup(query)
    end=time.time()
    diff=end-start
    for identifier,explanation in ans.iteritems():
        print "identifier '%s' because: %s"%(identifier,explanation)
    
    print ""
    print "execution time: %.4f"%diff
    sys.exit(0)