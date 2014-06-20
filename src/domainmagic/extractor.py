import re
from tld import get_IANA_TLD_list
import logging
import urlparse


def build_search_re(tldlist=None):
    if tldlist==None:
        tldlist=get_IANA_TLD_list()
    
    allowed_request_chars=r"-a-z0-9._/[\]?+%&="
    reg=r"(?:\b|(?<=:\"))" #start with boundary or " for href
    reg+=r"(?:https?://|ftp://)?" #protocol
    
    #TODO: username:pw@ ....
    
    #domain
    reg+=r"(?:" # domain types 
    
    #standard domain
    reg+=r"[-a-z0-9._]+" #TODO: all chars allowed in a domain
    reg+=r"(?:" #tldgroup
    reg+="|".join([x.replace('.','\.') for x in tldlist])
    reg+=r")"
    
    #dotquad
    reg+=r"|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    
    #TODO: ip6
    
    reg+=r")" # end of domain types
    
    #request
    reg+=r"(?:(?:" #optional stuff after domain
    reg+=r"/?["+allowed_request_chars+"]+" # TODO: all chars allowed in a request string
    reg+=r"|\/))?"
    reg+=r"(?=(?:[^"+allowed_request_chars+"]|$))" #non-uri character or end of line
    #print "RE: %s"%reg
    return re.compile(reg,re.IGNORECASE)



class URIExtractor():
    """Extract URIs"""

    searchre = None
    skiplist = []
    
    def __init__(self):
        #TODO: skiplist
        if URIExtractor.searchre==None:
            URIExtractor.searchre=build_search_re()
        self.logger=logging.getLogger('uriextractor')
        
    def load_skiplist(self,filename):
        URIExtractor.skiplist = self._load_single_file(filename)
    
    def _load_single_file(self,filename):
        """return lowercased list of unique entries"""
        if not os.path.exists(filename):
            self.logger.error("File %s not found - skipping"%filename)
            return []
        content=open(filename,'r').read().lower()
        entries=content.split()
        del content
        return set(entries)
        
    def extracturis(self,plaintext):
        uris=[]
        uris.extend(re.findall(URIExtractor.searchre, plaintext))
        
        finaluris=[]
        #check skiplist
        for uri in uris:
            checkuri=uri.lower()
            if '://' not in checkuri: #work around urlparse bug
                checkuri="http://%s"%uri
            domain=urlparse.urlparse(checkuri).netloc
            skip=False
            for skipentry in URIExtractor.skiplist:
                if domain==skip or domain.endswith(".%s"%skipentry):
                    skip=True
                    break
            
            if not skip:
                finaluris.append(uri)
        return sorted(set(finaluris))


if __name__=='__main__':
    extractor=URIExtractor()
    print extractor.extracturis("hello http://www.wgwh.ch/?doener lol yolo.com .")
     