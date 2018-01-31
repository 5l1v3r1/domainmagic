# -*- coding: utf-8 -*-
import unittest
import sys
sys.path.insert(0,'../src')
import domainmagic
from domainmagic.util import *

class UtilTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    
    def test_tld_list_to_tree(self):
        self.assertEquals(tld_list_to_tree(['foo','bar','baz']),{'foo': (False, {'bar': (False, {'baz': (True, {})})})})
    
    def test_tld_tree_update(self):
        d = {'foo': (True, {})}
        u = {'foo': (False, {'bar': (False, {'baz': (True, {})})})}
        exp = {'foo': (True, {'bar': (False, {'baz': (True, {})})})}
        t = tld_tree_update(d, u)
        self.assertEqual(t, exp)
    
    def test_tld_tree_path(self):
        d = {'foo': (True, {'bar': (False, {'baz': (True, {})})})}
        p = tld_tree_path(['foo', 'bar'], d)
        self.assertEqual(p, [('foo', True), ('bar', False)])
        p = tld_tree_path(['foo','bar','baz'], d)
        self.assertEqual(p, [('foo', True), ('bar', False), ('baz', True)])


    def test_list_to_dict(self):
        self.assertEquals(list_to_dict(['foo','bar','baz']),{'foo': {'bar': {'baz': {}}}})

    def test_dict_update(self):
        d={'foo':'bar'}
        update=dict(foo=dict(bar='baz'))
        dict_update(d,update)
        self.assertEquals(d,{'foo': {'bar': 'baz'}})

    def test_dict_path(self):
        tree=dict(foo=dict(bar='baz',bar2=dict(baz2='bam3')))
        self.assertEquals(dict_path(['foo','bar','baz','bam'],tree),['foo','bar','baz'])

    def test_combination(self):
        domain1=['doener','kebap','example','co.uk'][::-1]
        domain2=['foobar','co.uk'][::-1]
        domaintree={}
        dict_update(domaintree,list_to_dict(domain1))
        dict_update(domaintree,list_to_dict(domain2))
        self.assertEquals(domaintree, {'co.uk': {'foobar': {}, 'example': {'kebap': {'doener': {}}}}})

        self.assertEquals(dict_path(['co.uk','blubb'],domaintree),['co.uk'])
        self.assertEquals(dict_path(['co.uk','example'],domaintree),['co.uk','example'])
        self.assertEquals(dict_path(['com','example'],domaintree),[])


    def test_topdown_iterator(self):
        d={
            'co.uk': {'foobar': {}, 'example': {'kebap': {'doener': {}}}},
            'com':   {'foobar': {}, 'example': {'kebap': {'doener': {}}}},
           }

        result=[x for x in dict_topdown_iterator(d)]
        self.assertEquals(len(result),10)
        #check order
        prevlen=1
        for x in result:
            self.assertTrue(len(x)>=prevlen,"wrong topdown ordering: %s"%result)
            prevlen=len(x)