# -*- coding: utf-8 -*-
import unittest
from extractor import URIExtractor,domain_from_uri

class Extractor(unittest.TestCase):
    def setUp(self):
        self.candidate=URIExtractor()
        URIExtractor.skiplist=['skipme.com']
    
    def tearDown(self):
        pass
    
    
    def test_simple_text(self):
        txt="""hello http://bla.com please click on <a href="www.co.uk">slashdot.org/?a=c&f=m</a> www.skipme.com www.skipmenot.com/ x.co/4to2S http://allinsurancematters.net/lurchwont/ muahahaha x.org"""
        
        uris=self.candidate.extracturis(txt)
        self.assertTrue('http://bla.com' in uris, 'missing http://bla.com from %s, got only %s'%(txt,uris))
        self.assertTrue('www.co.uk' in uris)
        self.assertTrue('slashdot.org/?a=c&f=m' in uris)
        
        self.assertTrue('www.skipmenot.com/' in uris)
        #print " ".join(uris)
        self.assertTrue("skipme.com" not in " ".join(uris))
        
        self.assertTrue("http://allinsurancematters.net/lurchwont/" in uris)
        self.assertTrue("x.org" in uris,'rule at the end not found')
        self.assertTrue('x.co/4to2S','x.co short uri not found')
        
        
    def test_dotquad(self):
        txt="""click on 1.2.3.4 or http://62.2.17.61/ or https://8.8.8.8/bla.com """
        
        uris=self.candidate.extracturis(txt)
        self.assertTrue('1.2.3.4' in uris)
        self.assertTrue('http://62.2.17.61/' in uris)
        self.assertTrue('https://8.8.8.8/bla.com' in uris)
        
    def test_ipv6(self):
        txt="""click on http://[1337:1558:100b:1337:21b:21ff:fe9d:4e4a]/blah """
        
        uris=self.candidate.extracturis(txt)
        self.assertTrue('http://[1337:1558:100b:1337:21b:21ff:fe9d:4e4a]/blah' in uris,'ipv6 uri not extracted, got : %s'%uris)

        
    def test_uppercase(self):
        txt="""hello http://BLa.com please click"""
        uris=self.candidate.extracturis(txt)
        self.assertTrue('http://bla.com' not in uris,'uris should not be lowercased')
        self.assertTrue('http://BLa.com' in uris,'uri with uppercase not found')
        
    def test_url_without_file(self):
        txt="""lol http://roasty.familyhealingassist.ru?coil&commission blubb"""
        uris=self.candidate.extracturis(txt)
        self.assertTrue('http://roasty.familyhealingassist.ru?coil&commission' in uris,'did not find uri, result was %s'%uris)
        
    def test_negative(self):
        txt=""" yolo-hq.com&n=R3QY1V&c=0VZ1ND 1.2.3.4.5 1.2.3 2fwww.mktcompany.com.br%2forigem%2femail """
        uris=self.candidate.extracturis(txt)
        self.assertTrue(len(uris)==0,"Invalid uris should not have been extracted: %s"%uris)
        
    def test_usernamepw(self):
        txt=""" ftp://yolo:pw!_!@bla.com/blubb/bloing/baz.zip ftp://yolo@bla.com/blubb/bloing/baz.zip """
        uris=self.candidate.extracturis(txt)
        self.assertTrue('ftp://yolo:pw!_!@bla.com/blubb/bloing/baz.zip' in uris,'did not find uri with username and pw. result was %s'%uris)
        self.assertTrue('ftp://yolo@bla.com/blubb/bloing/baz.zip' in uris,'did not find uri with username. result was %s'%uris)
    