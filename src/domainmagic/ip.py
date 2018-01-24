# -*- coding: UTF-8 -*-
"""ip tools"""

from domainmagic.validators import is_ipv4, is_ipv6
from domainmagic.fileupdate import updatefile

try:
    import pygeoip
    PYGEOIP_AVAILABLE = True
except ImportError:
    PYGEOIP_AVAILABLE = False


def ip6_expand(ip):
    """remove :: shortcuts from ip adress - the returned address has 8 parts"""
    # TODO: there's probably a faster way to do this...

    # atm we only support plain ipv6 adresses
    if '.' in ip:
        raise ValueError()
    shortindex = ip.find('::')
    if shortindex < 0:
        return ip
    leading = ip[:shortindex]
    trailing = ip[shortindex + 2:]
    lparts = 0
    tparts = 0
    if leading:
        lparts = len(leading.split(':'))

    if trailing:
        tparts = len(trailing.split(':'))
    missingparts = 8 - lparts - tparts
    parts = ip.split(':')
    replace = ":".join(['0' for i in range(missingparts)])
    ret = ""
    if len(leading) > 0:
        ret += leading + ":"
    ret += replace
    if len(trailing) > 0:
        ret += ":" + trailing
    return ret


def ip_reversed(ip):
    """Return the reversed ip address representation for dns lookups"""
    if is_ipv4(ip):
        octets = ip.split('.')
        octets.reverse()
        return ".".join(octets)
    if is_ipv6(ip):
        expanded = ip6_expand(ip)
        parts = expanded.split(':')
        parts.reverse()
        return '.'.join(parts)

    raise ValueError("invalid ip address: %s" % ip)


@updatefile('/tmp/GeoIP.dat', 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz', refresh_time=24 * 3600, minimum_size=1000, unpack=True)
def geoip_country_code_by_addr(ip):
    assert PYGEOIP_AVAILABLE, "pygeoip is not installed"
    gi = pygeoip.GeoIP('/tmp/GeoIP.dat')
    retval = gi.country_code_by_addr(ip)
    return retval
