# -*- coding: UTF-8 -*-
from __future__ import print_function
import threading
from dns import resolver
from dns.rdatatype import to_text as rdatatype_to_text
from domainmagic.tasker import get_default_threadpool, TaskGroup, TimeOut
import time
import logging



class DNSLookupResult(object):

    def __init__(self):
        self.qtype = None
        self.question = None
        self.name = None
        self.content = None
        self.ttl = None
        self.rtype = None

    def __str__(self):
        return str(self.content)

    def __repr__(self):
        return "<type='%s' content='%s' ttl='%s'>" % (self.rtype, self.content, self.ttl)

    def __unicode__(self):
        return str(self.content).decode('utf-8')


def _make_results(question, qtype, resolveranswer):
    results = []
    for answer in resolveranswer:
        dnr = DNSLookupResult()
        dnr.question = question
        dnr.qtype = qtype
        dnr.content = answer.to_text()
        dnr.ttl = resolveranswer.rrset.ttl
        dnr.rtype = rdatatype_to_text(resolveranswer.rdtype)
        results.append(dnr)

    return results


class DNSLookup(object):
    MAX_PARALLEL_REQUESTS = 100

    semaphore = threading.Semaphore(MAX_PARALLEL_REQUESTS)

    def __init__(self, nameservers=None, timeout=3, lifetime=10):
        self.nameservers = nameservers

        if self.nameservers is None:
            self.resolver = resolver.Resolver()
        else:
            self.resolver = resolver.Resolver(configure=False)
            self.resolver.nameservers = self.nameservers
            # print self.resolver.nameservers

        self.resolver.timeout = timeout   # timeout for a individual request before retrying
        self.resolver.lifetime = lifetime  # max time for a request

        self.logger = logging.getLogger("%s.dnslookup" % __package__)

    def lookup(self, question, qtype='A'):
        """lookup one record returns a list of DNSLookupResult"""
        assert isinstance(question, str)

        resolveranswer = None

        try:
            DNSLookup.semaphore.acquire(False)
            self.logger.debug("query: %s/%s" % (question, qtype))
            resolveranswer = self.resolver.query(question, qtype)
            self.logger.debug(
                "query %s/%s completed -> %s" %
                (question, qtype, resolveranswer.rrset))
        except resolver.NXDOMAIN:
            pass
        except resolver.NoAnswer:
            pass
        except Exception as e:
            # TODO: some dnspython exceptions don't have a description - maybe add the full stack?
            self.logger.warning(
                "dnslookup %s/%s failed: %s: %s" %
                (question, qtype, e.__class__.__name__, str(e)))
        finally:
            DNSLookup.semaphore.release()

        if resolveranswer is not None:
            results = _make_results(question, qtype, resolveranswer)
            return results
        else:
            return []

    def lookup_multi(self, questions, qtype='A', timeout=10):
        """lookup a list of multiple records of the same qtype. the lookups will be done in parallel
        returns a dict question->[list of DNSLookupResult]
        """

        tg = TaskGroup()
        for question in questions:
            tg.add_task(self.lookup, args=(question, qtype))

        threadpool = get_default_threadpool()
        threadpool.add_task(tg)

        try:
            tg.join(timeout)
        except TimeOut:
            self.logger.warn('timeout in lookup_multi')
            pass

        result = {}
        for task in tg.tasks:
            if task.done:
                result[task.args[0]] = task.result
            else:
                self.logger.warn("hanging lookup: %s" % task)

        # print "lookup multi, questions=%s, qtype=%s ,
        # result=%s"%(questions,qtype,result)
        threadpool.stayalive = False

        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    d = DNSLookup()
    # print "Sync lookup:"
    # print d.lookup_sync('wgwh.ch')

    print("lookup start")
    start = time.time()
    result = d.lookup_multi(['wgwh.ch', 'heise.de', 'slashdot.org'])
    end = time.time()
    diff = end - start
    print("lookup end, time=%.4f" % diff)
    print(result)
