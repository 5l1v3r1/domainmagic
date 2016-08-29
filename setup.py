import sys
sys.path.insert(0,'src')
try:
    from setuptools import setup
except ImportError:
    from distutils import setup

from domainmagic import __version__
import glob


setup(name = "domainmagic",
    version = __version__,
    description = "Python library for all sorts of domain lookup related stuff (rbl lookups, extractors etc)",
    author = "O. Schacher",
    url='https://github.com/gryphius/domainmagic',
    author_email = "oli@wgwh.ch",
    package_dir={'':'src'},
    packages = ['domainmagic',],
    install_requires=[
        'dnspython',
        'pygeoip',
    ],
    long_description = """Python library for all sorts of domain lookup related stuff (rbl lookups, extractors etc)""" ,
    data_files=[
               ('/etc/domainmagic',glob.glob('conf/*.dist')),
    ],
    classifiers=[
          'Development Status :: 3 - Alpha',
          'Topic :: Internet :: Name Service (DNS)',
    ],
) 
