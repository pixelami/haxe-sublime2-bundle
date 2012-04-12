import sys
sys.path.append("/Users/a/Library/Application Support/Sublime Text 2/Packages/HaXe")
from hxutil import resolver
import datetime
import time

r = resolver.TypeDeclarationResolver()
print r


def testClassPathScan():
	starttime = datetime.datetime.now()
	print r.getTypeDeclarationsInClassPath("/Users/a/dev/sites/video.pixelami.com/src/haxe/")
	endtime = datetime.datetime.now()
	totaltime = endtime - starttime

	print "testClassPathScan: %s" % totaltime


testClassPathScan()
time.sleep(2)
testClassPathScan()

