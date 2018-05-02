# -*- coding: UTF-8 -*-
"""Validators"""
import re
import sys

if sys.version_info[0] >= 3:
    basestring = str


REGEX_IPV4 = """(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"""

REGEX_CIDRV4 = REGEX_IPV4 + """\/(?:[012]?[0-9]|3[0-2])"""

# from http://stackoverflow.com/questions/53497/regular-expression-that-matches-valid-ipv6-addresses
# with added dot escapes and removed capture groups
REGEX_IPV6 = """(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"""

REGEX_CIDRV6 = REGEX_IPV6 + """\/(?:12[0-8]|1[01][0-9]|[1-9]?[0-9])"""

# read doc and explanations in is_hostname
REGEX_HOSTNAME = """([_a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]?)(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*"""

REGEX_EMAIL_LHS = """[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"""


def _apply_rgx(rgx, content):
    if not isinstance(content, basestring):
        return False
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
    """
    Returns True if content is a valid hostname (but not necessarily a FQDN)
    
    a hostname label may start with underscore but cannot have an underscore at a later position
    a hostname label may contain dashes but not as first or last character
    a hostname label may only contain latin letters a-z and decimal numbers
    a hostname label must contain at least one character
    a hostname label must not exceed 63 characters
    a hostname should not exceed 255 characters (not covered by regex)
    more complex rules apply to FQDNs which are not covered by regex
    IDN is not covered by regex. convert to punycode first: u'idn-höstnäme.com'.encode('idna')
    
    :param content: the hostname to check
    :param check_valid_tld: set to True to only accept FQDNs with valid IANA approved TLD
    :param check_resolvable: set to True to only accept hostnames which can be resolved by DNS
    :return: True if valid hostname, False otherwise
    """
    if not isinstance(content, basestring):
        return False
    
    if not _apply_rgx(REGEX_HOSTNAME, content) or len(content) > 255:
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


def is_fqdn(content, check_valid_tld=False, check_resolvable=False):
    """
    Returns True if content is a valid FQDN
    
    Difference hostname vs FQDN:
    a hostname consists of at least one valid label
    a FQDN consist of at least two valid labels, thus contains a .
    
    :param content: the FQDN to check
    :param check_valid_tld: set to True to only accept FQDNs with valid IANA approved TLD
    :param check_resolvable: set to True to only accept FQDNs which can be resolved by DNS
    :return: True if valid FQDN, False otherwise
    """
    if not isinstance(content, basestring):
        return False
    
    if not '.' in content.strip('.'):
        return False
        
    if not is_hostname(content, check_valid_tld, check_resolvable):
        return False
    
    return True


def is_email(content, check_valid_tld=False, check_resolvable=False):
    """
    Returns True if content is a valid email address
    :param content: the email address to check
    :param check_valid_tld: set to True to only accept FQDNs with valid IANA approved TLD
    :param check_resolvable: set to True to only accept FQDNs which can be resolved by DNS
    :return: True if valid email address, False otherwise
    """
    if not isinstance(content, basestring):
        return False
    
    if not '@' in content:
        return False
    
    lhs, domain = content.rsplit('@', 1)
    
    if not _apply_rgx(REGEX_EMAIL_LHS, lhs):
        return False
    
    if not is_fqdn(domain, check_valid_tld, check_resolvable):
        return False
    
    return True


