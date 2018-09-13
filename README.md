domainmagic
===========

!! NOTE - domainmagic has moved to https://gitlab.com/fumail/domainmagic/ - This repository will no longer be updated and eventually deleted !!

domainmagic is a library which combines a bunch of domain/dns lookup tools and stuff often used in related applications

Overview
________

Generic features
________________

- parallel processing (threadpool, parallel dns lookups, ...)
- automatic file updates (geoip database, iana tld list, ...)


Domain/DNS/...
______________

- validator functions (ip adresses, hostnames, email addresses)
- uri and email address extraction
- tld/2tld/3tld handling
- rbl lookups
- geoIP 


Installation
____________

Supported version of Python:
- python 2.6
- python 2.7
- python 3.x (poorly tested)

Depencendies:
- pygeoip
- dnspython

```
python setup.py install
```


