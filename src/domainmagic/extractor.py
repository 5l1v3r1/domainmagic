import re
import os
import time
import logging
import urlparse

from tld import get_IANA_TLD_list
from validators import REGEX_IPV4, REGEX_IPV6
import traceback


def build_search_re(tldlist=None):
    if tldlist==None:
        tldlist=get_IANA_TLD_list()
    
    allowed_request_chars=r"-a-z0-9;._/[\]?#+%&="
    reg=r"(?:\b|(?<=:\"))" #start with boundary or " for href
    reg+=r"(?:https?://|ftp://)?" #protocol
    
    #TODO: username:pw@ ....
    
    #domain
    reg+=r"(?:" # domain types 
    
    #standard domain
    reg+=r"[-a-z0-9._]+\." #hostname
    reg+=r"(?:" #tldgroup
    reg+="|".join([x.replace('.','\.') for x in tldlist])
    reg+=r")\b"
    
    #dotquad
    reg+=r"|%s"%REGEX_IPV4
    
    #ip6
    reg+=r"|\[%s\]"%REGEX_IPV6
    
    reg+=r")" # end of domain types
    
    #request
    reg+=r"(?:(?:" #optional stuff after domain
    reg+=r"\/?" # optional / at end of domain
    reg+=r"(?=[^&])" # lookahead: & is not allowed here, this filters false positives if the domain is in a borked request string, eg "....bla.com&blubb=bloing"
    reg+="["+allowed_request_chars+"]+" # TODO: all chars allowed in a request string
    reg+=r"|\/))?"
    reg+=r"(?=(?:[^"+allowed_request_chars+"]|$))" #non-uri character or end of line
    #print "RE: %s"%reg
    return re.compile(reg,re.IGNORECASE)


def build_email_re(tldlist=None):
    if tldlist==None:
        tldlist=get_IANA_TLD_list()
    
    reg=r"(?=.{0,64}\@)"                         # limit userpart to 64 chars
    reg+=r"(?<![a-z0-9!#$%&'*+\/=?^_`{|}~-])"     # start boundary
    reg+=r"("                                             # capture email
    reg+=r"[a-z0-9!#$%&'*+\/=?^_`{|}~-]+"         # no dot in beginning
    reg+=r"(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*"  # no consecutive dots, no ending dot
    reg+=r"\@"
    reg+=r"[-a-z0-9._]+\." #hostname
    reg+=r"(?:" #tldgroup
    reg+="|".join([x.replace('.','\.') for x in tldlist])
    reg+=r")"
    reg+=r")(?!(?:[a-z0-9-]|\.[a-z0-9]))"          # make sure domain ends here
    return re.compile(reg,re.IGNORECASE)

    
def domain_from_uri(uri):
    """extract the domain(fqdn) from uri"""
    if '://' not in uri:
        uri="http://"+uri
    domain=urlparse.urlparse(uri.lower()).netloc
    return domain

class URIExtractor(object):
    """Extract URIs"""

    searchre = None
    emailre = None
    skiplist = []
    maxregexage=86400 #rebuild search regex once a day so we get new tlds
    
    def __init__(self):
        #TODO: skiplist
        self.lastreload=time.time()
        self.lastreloademail=time.time()
        if URIExtractor.searchre==None:
            URIExtractor.searchre=build_search_re()
        if URIExtractor.emailre==None:
            URIExtractor.emailre=build_email_re()
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
        if time.time()-self.lastreload>URIExtractor.maxregexage:
            self.lastreload=time.time()
            self.logger.debug("Rebuilding search regex with latest TLDs")
            try:
                URIExtractor.searchre=build_search_re()
            except Exception,e:
                self.logger.error("Rebuilding search re failed: %s"%traceback.format_exc())
                
        
        uris=[]
        uris.extend(re.findall(URIExtractor.searchre, plaintext))
        
        finaluris=[]
        #check skiplist$
        for uri in uris:
            try:
                domain=domain_from_uri(uri.lower())
            except Exception,e:
                #self.logger.warn("Extract domain from uri %s failed : %s"%(uri,str(e)))
                continue
                   
            #work around extractor bugs - these could probably also be fixed in the search regex
            #but for now it's easier to just throw them out
            if '..' in domain: #two dots in domain
                continue
            
            if uri.endswith(']'): # 1.2.3.4]
                if re.match("^%s$"%REGEX_IPV4,uri[:-1]) is not None:
                    uri=uri[:-1]
            
            if re.match("^(?:\d{1,3}\.){3}(?:\d{1,3})(?:\.\d{1,3})+$",uri) is not None: # 1.2.3.4.5
                continue
            
            
            skip=False
            for skipentry in URIExtractor.skiplist:
                if domain==skip or domain.endswith(".%s"%skipentry):
                    skip=True
                    break            
            if not skip:
                finaluris.append(uri)
        return sorted(set(finaluris))

    def extractemails(self,plaintext):
        if time.time()-self.lastreloademail>URIExtractor.maxregexage:
            self.lastreloademail=time.time()
            self.logger.debug("Rebuilding search regex with latest TLDs")
            try:
                URIExtractor.emailre=build_email_re()
            except Exception,e:
                self.logger.error("Rebuilding email search re failed: %s"%traceback.format_exc())
                
        emails=[]
        emails.extend(re.findall(URIExtractor.emailre, plaintext))
        return sorted(set(emails))

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    extractor=URIExtractor()
    logging.info(extractor.extracturis("hello http://www.wgwh.ch/?doener lol yolo.com ."))
    
    logging.info(extractor.extractemails("blah a@b.com someguy@gmail.com"))
    
    
    
    