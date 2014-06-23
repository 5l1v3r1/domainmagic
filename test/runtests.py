#!/usr/bin/python

import unittest
import sys
import logging
import logging.config
import ConfigParser
import os
import datetime

#make sure working dir is set to the directory where runtests.py resides
import inspect
this_file = inspect.currentframe().f_code.co_filename
workdir=os.path.dirname(os.path.abspath(this_file))
os.chdir(workdir)

sys.path.insert(0,'../src/domainmagic')

#overwrite logger
console = logging.StreamHandler()
console.setLevel(logging.INFO)
consoleformatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(consoleformatter)

start=datetime.datetime.now()
startstr=start.strftime("%Y-%m-%d_%H:%M:%S")
logfile='/tmp/scraper-test.log'

filelogger=logging.FileHandler(logfile, 'w')
filelogger.setLevel(logging.DEBUG)
fileformatter=logging.Formatter("%(asctime)s %(name)-12s: %(levelname)s %(message)s")
filelogger.setFormatter(fileformatter)

rootlogger=logging.getLogger('')
rootlogger.setLevel(logging.DEBUG)
rootlogger.addHandler(console)
rootlogger.addHandler(filelogger)



#don't allow the test subject to screw with our log config
def loggingdummy(*args,**kwargs):
    rootlogger.warn("override of log config denied by test framework.")
logging.config.fileConfig=loggingdummy


rootlogger.info("#Tests starting at %s"%startstr)



testonly=None
if len(sys.argv)>1:
    testonly=sys.argv[1:]

loader=unittest.TestLoader()
alltests=unittest.TestSuite()

modules=[
 'testmodules.t_extractor',

]

for mod in modules:
    if testonly!=None and mod not in testonly:
        continue
    if mod==None or mod=='':
        continue
    ldmod=__import__(mod)
    suite=loader.loadTestsFromName(mod)
    count=suite.countTestCases()
    print "found %s tests in %s"%(count,mod)
    alltests.addTests(suite)
print "---------------------------"
print "Total %s tests in Testsuite"%alltests.countTestCases()
print ""
print "STARTING TESTS"
print ""

runner=unittest.TextTestRunner()
result=runner.run(alltests)

print ""
print "Debug Output written to:%s"%logfile

if result.wasSuccessful():
    print "ALL TESTS SUCCESSFUL"
    sys.exit(0)
else:
    print "TESTRUN FAILED"
    sys.exit(1)