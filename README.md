domainmagic is a library which combines a bunch of domain/dns lookup tools and stuff often used in related applications

Overview
________

Generic features
________________

- parallel processing (threadpool , parallel dns lookups, ...)
- automatic file updates (geoip database, iana tld list, ...)


Domain/DNS/...
______________

- validator functions (ip adresses)
- uri extraction
- tld/2tld/3tld handling
- rbl lookups
- geoIP 


Installation
____________

Depencendies:
 - pygeoip
 - dnspython

```
python setup.py install
```


