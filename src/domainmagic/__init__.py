# -*- coding: UTF-8 -*-
__version__ = "0.0.9"


def check_installation():
    """check dependencies , returns a list of problems"""
    problems = []

    from domainmagic.ip import PYGEOIP_AVAILABLE

    if not PYGEOIP_AVAILABLE:
        problems.append("pygeoip is not installed - geoip functions disabled")

    try:
        from dns import resolver
    except ImportError:
        problems.append("dnspython is not installed")

    return problems
