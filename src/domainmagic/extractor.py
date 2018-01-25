# -*- coding: UTF-8 -*-
import re
import os
import time
import logging
from domainmagic.tld import get_IANA_TLD_list
from domainmagic.validators import REGEX_IPV4, REGEX_IPV6
import traceback
import io
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse
    
    
EMAIL_HACKS = {
    '@' : ['(at)', ' (at) ', ' AT ', '[at]'],
    '.' : ['(dot)', ' (dot) ', ' DOT ', '[dot]'],
}


def build_search_re(tldlist=None):
    if tldlist is None:
        tldlist = get_IANA_TLD_list()

    # lookbehind to check for start of url
    # start with
    # - start of string
    # - whitespace
    # - " for href
    # - ' for borked href
    # - > for links in tags
    # - ) after closing parentheses (seen in chinese spam)
    # - * seen in spam
    # - - seen in spam
    reg = r"(?:(?<=^)|(?<="
    reg += r"(?:\s|[\"'\>\)\*-])"
    reg += r"))"

    # url starts here
    reg += r"(?:"
    reg += r"(?:https?://|ftp://)"  # protocol
    reg += r"(?:[a-z0-9!%_$]+(?::[a-z0-9!%_$]+)?@)?"  # username/pw
    reg += r")?"

    # domain
    reg += r"(?:"  # domain types

    # standard domain
    allowed_hostname_chars = r"-a-z0-9_"
    reg += r"[a-z0-9_]"  # first char can't be a hyphen
    reg += r"[" + allowed_hostname_chars + \
        r"]*"  # there are domains with only one character, like 'x.org'
    reg += r"(?:\.[" + allowed_hostname_chars + \
        r"]+)*"  # more hostname parts separated by dot
    reg += r"\."  # dot between hostname and tld
    reg += r"(?:"  # tldgroup
    reg += r"|".join([x.replace('.', '\.') for x in tldlist])
    reg += r")\.?"  # standard domain can end with a dot

    # dotquad
    reg += r"|%s" % REGEX_IPV4

    # ip6
    reg += r"|\[%s\]" % REGEX_IPV6

    reg += r")"  # end of domain types

    # optional port
    reg += r"(?:\:\d{1,5})?"

    # after the domain, there must be a path sep or quotes space or ? end,
    # check with lookahead
    reg += r"""(?=["'/?]|\s|$)"""

    # path
    allowed_path_chars = r"-a-z0-9._/%#\[\]~*"
    reg += r"(?:\/[" + allowed_path_chars + r"]+)*"

    # request params
    allowed_param_chars = r"-a-z0-9;._/\[\]?#+%&=@*"
    reg += r"(?:\/?)"  # end domain with optional  slash
    reg += r"(?:\?[" + allowed_param_chars + \
        r"]*)?"  # params must follow after a question mark

    # print "RE: %s"%reg
    return re.compile(reg, re.IGNORECASE)


def build_email_re(tldlist=None):
    if tldlist is None:
        tldlist = get_IANA_TLD_list()

    reg = r"(?=.{0,64}\@)"                         # limit userpart to 64 chars
    reg += r"(?<![a-z0-9!#$%&'*+\/=?^_`{|}~-])"     # start boundary
    reg += r"("                                             # capture email
    reg += r"[a-z0-9!#$%&'*+\/=?^_`{|}~-]+"         # no dot in beginning
    reg += r"(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*"  # no consecutive dots, no ending dot
    reg += r"\@"
    reg += r"[-a-z0-9._]+\."  # hostname
    reg += r"(?:"  # tldgroup
    reg += r"|".join([x.replace('.', '\.') for x in tldlist])
    reg += r")"
    reg += r")(?!(?:[a-z0-9-]|\.[a-z0-9]))"          # make sure domain ends here
    return re.compile(reg, re.IGNORECASE)


def domain_from_uri(uri):
    """backwards compatibilty name"""
    return fqdn_from_uri(uri)


def fqdn_from_uri(uri):
    """extract the domain(fqdn) from uri"""
    if '://' not in uri:
        uri = "http://" + uri
    fqdn = urlparse.urlparse(uri.lower()).netloc

    # remove port
    portmatch = re.search(':\d{1,5}$', fqdn)
    if portmatch is not None:
        fqdn = fqdn[:portmatch.span()[0]]

    return fqdn


def redirect_from_google(uri):
    """extract target domain from google redirects"""
    parsed = urlparse.urlparse(uri)
    if 'google.' in parsed.netloc and parsed.path == '/url':
        values = urlparse.parse_qs(parsed.query)
        for key in ['q', 'url']:
            uris = values.get(key, [])
            if len(uris) > 0:
                uri = uris[0] # we expect exactly one redirect
    return uri


class URIExtractor(object):

    """Extract URIs"""

    def __init__(self, tldlist=None):
        # TODO: skiplist
        self.tldlist = tldlist
        self.lastreload = time.time()
        self.lastreloademail = time.time()
        self.logger = logging.getLogger('%s.uriextractor' % __package__)
        self.searchre = build_search_re(self.tldlist)
        self.emailre = build_email_re(self.tldlist)
        self.skiplist = []
        self.maxregexage = 86400  # rebuild search regex once a day so we get new tlds
    
    
    def set_tld_list(self, tldlist):
        """override the tldlist and rebuild the search regex"""
        self.tldlist = tldlist
        self.searchre = build_search_re(tldlist)
        self.emailre = build_email_re(tldlist)
    
    
    def load_skiplist(self, filename):
        self.skiplist = self._load_single_file(filename)
    
    
    def _load_single_file(self, filename):
        """return lowercased list of unique entries"""
        if not os.path.exists(filename):
            self.logger.error("File %s not found - skipping" % filename)
            return []
        with io.open(filename, 'r') as f:
            content = f.read().lower()
        entries = content.split()
        del content
        return set(entries)
    
    
    def _uri_filter(self, uri, use_hacks):
        skip = False
        newuri = None
        try:
            domain = fqdn_from_uri(uri.lower())
        except Exception:
            skip = True
            domain = None
    
        # work around extractor bugs - these could probably also be fixed in the search regex
        # but for now it's easier to just throw them out
        if not skip and domain and '..' in domain:  # two dots in domain
            skip = True
    
        if not skip and use_hacks:
            newuri = redirect_from_google(uri)
    
        skip = False
        for skipentry in self.skiplist:
            if domain == skip or domain.endswith(".%s" % skipentry):
                skip = True
                break
    
        # axb: trailing dots are probably not part of the uri
        if uri.endswith('.'):
            uri = uri[:-1]
            
        return skip, uri, newuri
    
    
    def extracturis(self, plaintext, use_hacks=False):
        if self.tldlist is None and time.time() - self.lastreload > self.maxregexage:
            self.lastreload = time.time()
            self.logger.debug("Rebuilding search regex with latest TLDs")
            try:
                self.searchre = build_search_re()
            except Exception:
                self.logger.error(
                    "Rebuilding search re failed: %s" %
                    traceback.format_exc())

        uris = []
        uris.extend(re.findall(self.searchre, plaintext))

        finaluris = []
        # check skiplist and apply recursive extraction hacks
        for newuri in uris:
            while newuri is not None:
                skip, uri, newuri = self._uri_filter(newuri, use_hacks)
                if newuri == uri:
                    newuri = None
                if not skip:
                    finaluris.append(uri)
            
        return sorted(set(finaluris))
    
    
    def extractemails(self, plaintext, use_hacks=False):
        if time.time() - self.lastreloademail > self.maxregexage:
            self.lastreloademail = time.time()
            self.logger.debug("Rebuilding search regex with latest TLDs")
            try:
                self.emailre = build_email_re()
            except Exception:
                self.logger.error(
                    "Rebuilding email search re failed: %s" %
                    traceback.format_exc())
        
        if use_hacks:
            for key in EMAIL_HACKS:
                for value in EMAIL_HACKS[key]:
                    plaintext = plaintext.replace(value, key)
        
        emails = []
        emails.extend(re.findall(self.emailre, plaintext))
        return sorted(set(emails))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    extractor = URIExtractor()
    # logging.info(extractor.extracturis("hello http://www.wgwh.ch/?doener lol
    # yolo.com . blubb.com."))

    # logging.info(extractor.extractemails("blah a@b.com someguy@gmail.com"))

    txt = """hello http://bla.com please click on <a href="www.co.uk">slashdot.org/?a=c&f=m</a> www.skipme.com www.skipmenot.com/ x.co/4to2S http://allinsurancematters.net/lurchwont/ muahahaha x.org"""
    logging.info(extractor.extracturis(txt))
