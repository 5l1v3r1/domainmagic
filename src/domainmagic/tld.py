# -*- coding: UTF-8 -*-
from __future__ import print_function
from util import dict_update, dict_path, list_to_dict
import re
from fileupdate import updatefile


@updatefile('/tmp/tlds-alpha-by-domain.txt', 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt', minimum_size=1000, refresh_time=86400, force_recent=True)
def get_IANA_TLD_list():
    tlds = []
    content = open('/tmp/tlds-alpha-by-domain.txt').readlines()
    for line in content:
        if line.strip() == '' or line.startswith('#'):
            continue
        tlds.extend(line.lower().split())
    return list(sorted(tlds))


default_tldmagic = None


def get_default_tldmagic():
    global default_tldmagic
    if default_tldmagic is None:
        default_tldmagic = TLDMagic()
    return default_tldmagic


def load_tld_file(filename):
    retval = []
    for line in open(filename, 'r').readlines():
        if line.startswith('#') or line.strip() == '':
            continue
        tlds = line.split()
        for tld in tlds:
            if tld.startswith('.'):
                tld = tld[1:]
            tld = tld.lower()
            if re.match('^[a-z0-9\-.]{2,64}$', tld):
                if tld not in retval:
                    retval.append(tld)
    return retval


class TLDMagic(object):

    def __init__(self, initialtldlist=None):
        self.tldtree = {}  # store
        if initialtldlist is None:
            self._add_iana_tlds()
        else:
            for tld in initialtldlist:
                self.add_tld(tld)

    def _add_iana_tlds(self):
        for tld in get_IANA_TLD_list():
            self.add_tld(tld)

    def get_tld(self, fqdn):
        """get the tld from domain, returning the largest possible xTLD"""
        fqdn = fqdn.lower()
        parts = fqdn.split('.')
        parts.reverse()
        tldparts = dict_path(parts, self.tldtree)
        if len(tldparts) == 0:
            return None
        tldparts.reverse()
        tld = '.'.join(tldparts)
        return tld

    def get_tld_count(self, fqdn):
        """returns the number of tld parts for domain, eg.
        example.com -> 1
        bla.co.uk -> 2"""
        tld = self.get_tld(fqdn)
        if tld is None:
            return 0
        return len(self.get_tld(fqdn).split('.'))

    def get_domain(self, fqdn):
        """returns the domain name with all subdomains stripped.
         eg, TLD + one label
         """
        hostlabels, tld = self.split(fqdn)
        if len(hostlabels) > 0:
            return "%s.%s" % (hostlabels[-1], tld)
        else:
            return tld

    def split(self, fqdn):
        """split the fqdn into hostname labels and tld. returns a 2-tuple, the first element is a list of hostname lablels, the second element is the tld
        eg.: foo.bar.baz.co.uk returns (['foo','bar','baz'],'co.uk')
        """
        tldcount = self.get_tld_count(fqdn)
        labels = fqdn.split('.')
        return labels[:-tldcount], '.'.join(labels[-tldcount:])

    def add_tld(self, tld):
        """add a new tld to the list"""
        tld = tld.lower()
        parts = tld.split('.')
        parts.reverse()
        update = list_to_dict(parts)
        self.tldtree = dict_update(self.tldtree, update)

    def add_tlds_from_file(self, filename):
        for tld in load_tld_file(filename):
            self.add_tld(tld)


if __name__ == '__main__':
    t = TLDMagic()
    t.add_tld('bay.livefilestore.com')
    t.add_tld('co.uk')

    for test in ['kaboing.bla.bay.livefilestore.com', 'yolo.doener.com', 'blubb.co.uk', 'bloing.bazinga', 'co.uk']:
        print("'%s' -> '%s'" % (test, t.get_tld(test)))
