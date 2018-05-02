# -*- coding: utf-8 -*-
import unittest
import sys
sys.path.insert(0,'../src')
import domainmagic
from domainmagic.validators import *

class ValidatorTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    
    
    def test_ipv4(self):
        valid_data = ['0.0.0.0', '255.255.255.255', '127.0.0.1', '8.8.8.8']
        invalid_data = ['0.0.0', '0.0.0.0.0', '256.0.0.0', 'example.com']
        for item in valid_data:
            self.assertTrue(is_ipv4(item), 'unmatched value %s' % item)
        for item in invalid_data:
            self.assertFalse(is_ipv4(item), 'matched value %s' % item)
    
    
    
    def test_ipv6(self):
        valid_data = ['::', '::1', '2001:beef::1', 'fe80::1ce:1ce:babe', '2a02:dead:beef:0:1:5ee:bad:c0de', '1:2:3:4:5:6:7:8']
        invalid_data = ['2001:best:data::1', '2001:aaaaa::1', '1:2:3:4:5:6:7:8:9', 'example.com']
        for item in valid_data:
            self.assertTrue(is_ipv6(item), 'unmatched value %s' % item)
        for item in invalid_data:
            self.assertFalse(is_ipv6(item), 'matched value %s' % item)
    
    
    
    def test_hostname(self):
        valid_data = ['hostname', 'example.com', 'foo.example.com', '_f-o.example.com', 'a.example.com']
        invalid_data = ['-bla.example.com', 'foo._example.com', 'f_o.example.com', 'this-is-a-very-long-host-name-beyond-sixty-three-character-label-length.example.com', 'very-long-host-name.beyond-two-hundred-fifty-five-character.total-length.with-lots-of-filler-data.aaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaa.example.com']
        for item in valid_data:
            self.assertTrue(is_hostname(item), 'unmatched value %s' % item)
        for item in invalid_data:
            self.assertFalse(is_hostname(item), 'matched value %s' % item)