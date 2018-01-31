# -*- coding: UTF-8 -*-
from __future__ import print_function
from domainmagic.util import tld_tree_update, tld_list_to_tree, tld_tree_path
from domainmagic.fileupdate import updatefile
import io
import re


@updatefile('/tmp/tlds-alpha-by-domain.txt', 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt', minimum_size=1000, refresh_time=86400, force_recent=True)
def get_IANA_TLD_list():
    tlds = []
    with io.open('/tmp/tlds-alpha-by-domain.txt') as fp:
        content = fp.readlines()
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
    with io.open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines:
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
        candidates = tld_tree_path(parts, self.tldtree)
        if len(candidates) == 0:
            return None
        candidates.reverse()
        tldparts = []
        leaf = False
        for part in candidates:
            if part[1]:
                leaf = True
            if leaf:
                tldparts.append(part[0])
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
        tld = tld.lower().strip('.')
        parts = tld.split('.')
        parts.reverse()
        update = tld_list_to_tree(parts)
        self.tldtree = tld_tree_update(self.tldtree, update)

    def add_tlds_from_file(self, filename):
        for tld in load_tld_file(filename):
            self.add_tld(tld)


if __name__ == '__main__':
    t = TLDMagic()
    t.add_tld('bay.livefilestore.com')
    t.add_tld('co.uk')

    for test in ['kaboing.bla.bay.livefilestore.com', 'yolo.doener.com', 'blubb.co.uk', 'bloing.bazinga', 'co.uk']:
        print("'%s' -> '%s'" % (test, t.get_tld(test)))
