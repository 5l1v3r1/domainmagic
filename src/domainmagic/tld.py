
from domainmagic import updatefile


@updatefile('/tmp/tlds-alpha-by-domain.txt','http://data.iana.org/TLD/tlds-alpha-by-domain.txt',minimum_size=1000)
def get_IANA_TLD_list():
    tlds=[]
    content=open('/tmp/tlds-alpha-by-domain.txt').readlines()
    for line in content:
        if line.strip()=='' or line.startswith('#'):
            continue
        tlds.extend(line.lower().split())
    return list(sorted(tlds))
    



