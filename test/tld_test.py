# -*- coding: utf-8 -*-
import unittest
import sys
sys.path.insert(0,'../src')
import domainmagic
from domainmagic.tld import TLDMagic

class UtilTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_tld_count(self):
        tldmagic = TLDMagic(['com','co.uk','org.co.uk'])
        testdata=[
            ('bla.com',1),
            ('co.uk',2),
            ('bla.co.uk',2),
            ('bla.blubb.co.uk',2),
            ('bla.org.co.uk',3),
        ]
        for fqdn,expectedtldcount in testdata:
            count = tldmagic.get_tld_count(fqdn)
            self.assertEqual(count,expectedtldcount, "Expected TLD count %s from %s, but got %s"%(expectedtldcount,fqdn,count))

    def test_get_tld(self):
        tldmagic = TLDMagic(['com','co.uk','org.co.uk'])
        testdata=[
            ('bla.com','com'),
            ('co.uk','co.uk'),
            ('bla.co.uk','co.uk'),
            ('bla.blubb.co.uk','co.uk'),
            ('bla.org.co.uk','org.co.uk'),
        ]
        for fqdn,expectedtld in testdata:
            tld = tldmagic.get_tld(fqdn)
            self.assertEqual(tld,expectedtld, "Expected TLD %s from %s, but got %s"%(expectedtld,fqdn,tld))
    
    
    def test_get_3tld_no_2tld(self):
        tldmagic = TLDMagic(['com', 'three.ex.com'])
        testdata=[
            ('bla.com','com'),
            ('ex.com','com'),
            ('three.ex.com','three.ex.com'),
            ('bla.three.ex.com','three.ex.com'),
        ]
        for fqdn,expectedtld in testdata:
            tld = tldmagic.get_tld(fqdn)
            self.assertEqual(tld,expectedtld, "Expected TLD %s from %s, but got %s"%(expectedtld,fqdn,tld))
            

    def test_get_domain(self):
        tldmagic = TLDMagic(['com','co.uk','org.co.uk'])
        testdata=[
            ('bla.com','bla.com'),
            ('co.uk','co.uk'),
            ('bla.co.uk','bla.co.uk'),
            ('bla.blubb.co.uk','blubb.co.uk'),
            ('bla.org.co.uk','bla.org.co.uk'),
        ]
        for fqdn,expecteddomain in testdata:
            domain = tldmagic.get_domain(fqdn)
            self.assertEqual(domain,expecteddomain, "Expected Domain %s from %s, but got %s"%(expecteddomain,fqdn,domain))