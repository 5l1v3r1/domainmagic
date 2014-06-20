import sys
sys.path.insert(0,'src')
from distutils.core import setup
from domainmagic import VERSION
import glob


setup(name = "domainmagic",
    version = VERSION,
    description = "Python library for all sorts of domain lookup related tuff (rbl lookups, extractors etc)",
    author = "O. Schacher",
    url='',
    author_email = "oli@wgwh.ch",
    package_dir={'':'src'},
    packages = ['domainmagic',],
    long_description = """Python library for all sorts of domain lookup related tuff (rbl lookups, extractors etc)""" ,
    data_files=[
               ('/etc/domainmagic',glob.glob('conf/*.dist')),
    ]
) 
