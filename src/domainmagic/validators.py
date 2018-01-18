# -*- coding: UTF-8 -*-
"""Validators"""
import re


REGEX_IPV4 = """(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"""

REGEX_CIDRV4 = REGEX_IPV4 + """\/(?:[012]?[0-9]|3[0-2])"""

# from http://stackoverflow.com/questions/53497/regular-expression-that-matches-valid-ipv6-addresses
# with added dot escapes and removed capture groups
REGEX_IPV6 = """(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"""

REGEX_CIDRV6 = REGEX_IPV6 + """\/(?:12[0-8]|1[01][0-9]|[1-9]?[0-9])"""

REGEX_HOSTNAME = """^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$"""

REGEX_EMAIL_LHS = """^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*$"""


def _apply_rgx(rgx, content):
    return re.match("^%s$" % rgx, content) is not None



def is_ipv4(content):
    """Returns True if content is a valid IPv4 address, False otherwise"""
    return _apply_rgx(REGEX_IPV4, content)


def is_cidrv4(content):
    """Returns True if content is a valid IPv4 CIDR, False otherwise"""
    return _apply_rgx(REGEX_CIDRV4, content)


def is_ipv6(content):
    """Returns True if content is a valid IPv6 address, False otherwise"""
    return _apply_rgx(REGEX_IPV6, content)


def is_cidrv6(content):
    """Returns True if content is a valid IPv6 CIDR, False otherwise"""
    return _apply_rgx(REGEX_CIDRV6, content)


def is_ip(content):
    """Returns True if content is a valid IPV4 or IPv6 address, False otherwise"""
    return is_ipv4(content) or is_ipv6(content)


def is_hostname(content, check_valid_tld=False, check_resolvable=False):
    if not _apply_rgx(REGEX_HOSTNAME, content):
        return False

    if check_valid_tld:
        from domainmagic.tld import get_default_tldmagic
        if get_default_tldmagic().get_tld(content) is None:
            return False
    
    if check_resolvable:
        from domainmagic.dnslookup import DNSLookup
        dns = DNSLookup()
        for qtype in ['A', 'AAAA', 'MX', 'NS']:
            result = dns.lookup(content, qtype)
            if len(result)>0:
                break
        else:
            return False

    return True


def is_email(content, check_valid_tld=False, check_resolvable=False):
    if not '@' in content:
        return False
    
    lhs, domain = content.split('@', 1)
    
    if not is_hostname(domain, check_valid_tld, check_resolvable):
        return False
    
    if not _apply_rgx(REGEX_EMAIL_LHS, lhs):
        return False
    
    return True


