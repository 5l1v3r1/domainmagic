
from domainmagic import updatefile
import collections
import re


@updatefile('/tmp/tlds-alpha-by-domain.txt','http://data.iana.org/TLD/tlds-alpha-by-domain.txt',minimum_size=1000,refresh_time=86400,force_recent=True)
def get_IANA_TLD_list():
    tlds=[]
    content=open('/tmp/tlds-alpha-by-domain.txt').readlines()
    for line in content:
        if line.strip()=='' or line.startswith('#'):
            continue
        tlds.extend(line.lower().split())
    return list(sorted(tlds))


global default_tldmagic
default_tldmagic=None

def get_default_tldmagic():
    global default_tldmagic
    if default_tldmagic==None:
        default_tldmagic=TLDMagic()
    return default_tldmagic


def load_tld_file(filename):
    retval=[]
    for line in open(filename,'r').readlines():
        if line.startswith('#') or line.strip()=='':
            continue
        tlds=line.split()
        for tld in tlds:
            if tld.startswith('.'):
                tld=tld[1:]
            tld=tld.lower()
            if re.match('^[a-z0-9\-\.]+$',tld):
                if tld not in retval:
                    retval.append(tld)
    return retval

class TLDMagic(object):
    def __init__(self,initialtldlist=None):
        self.tldtree={} #store
        if initialtldlist==None:
            self._add_iana_tlds()
        else:
            for tld in initialtldlist:
                self.add_tld(tld)
        
    def _add_iana_tlds(self):
        for tld in get_IANA_TLD_list():
            self.add_tld(tld)
    
    def get_tld(self,domain):
        """get the tld from domain, returning the largest possible xTLD"""
        domain=domain.lower()
        parts=domain.split('.')
        parts.reverse()
        tldparts=self._walk(parts,self.tldtree)
        if len(tldparts)==0:
            return None
        tldparts.reverse()
        tld= '.'.join(tldparts)
        return tld
    
    def get_tld_count(self,domain):
        """returns the number of tld parts for domain, eg.
        example.com -> 1
        bla.co.uk -> 2"""
        tld=self.get_tld(domain)
        if tld==None:
            return 0
        return len(self.get_tld(domain).split('.'))

    def split(self,domain):
        """split the domain into hostname labels and tld. returns a 2-tuple, the first element is a list of hostname lablels, the second element is the tld
        eg.: foo.bar.baz.co.uk returns (['foo','bar','baz'],'co.uk')
        """
        tldcount=self.get_tld_count(domain)
        labels=domain.split('.')
        return labels[:-tldcount],'.'.join(labels[-tldcount:])
    
    def _walk(self,l,node,path=None):
        """walk list l through dict l and return a list of all nodes found up until a leaf node"""
        if path==None:
            path=[]
        
        if len(l)==0:
            return path
        
        if l[0] in node:
            path.append(l[0])
            return self._walk(l[1:],node[l[0]],path)
        
        return path
                
    def _dict_update(self,d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = self._dict_update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d
    
    def _list_to_dict(self,l):
        """translate a list into a tree path"""
        d={}
        if len(l)==0:
            return d
        else:
            d[l[0]]=self._list_to_dict(l[1:])
            return d

    def add_tld(self,tld):
        """add a new tld to the list"""
        tld=tld.lower()
        parts=tld.split('.')
        parts.reverse()
        update=self._list_to_dict(parts)
        self.tldtree=self._dict_update(self.tldtree, update)

    def add_tlds_from_file(self,filename):
        for tld in load_tld_file(filename):
            self.add_tld(tld)
            
    
    
if __name__ == '__main__':
    t = TLDMagic()
    t.add_tld('bay.livefilestore.com')
    t.add_tld('co.uk')
    
    for test in ['kaboing.bla.bay.livefilestore.com','yolo.doener.com','blubb.co.uk','bloing.bazinga']:
        print "'%s' -> '%s'"%(test,t.get_tld(test))
    