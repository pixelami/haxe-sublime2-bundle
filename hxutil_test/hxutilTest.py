import sys
import os
sys.path.append("/Users/a/Library/Application Support/Sublime Text 2/Packages/HaXe")
from hxutil import resolver
import datetime
import time


r = resolver.TypeDeclarationResolver()


def testClassPathScan():
	starttime = datetime.datetime.now()
	print r.getTypeDeclarationsInClassPath("/Users/a/dev/sites/video.pixelami.com/src/haxe/")
	endtime = datetime.datetime.now()
	totaltime = endtime - starttime
	print "testClassPathScan: %s" % totaltime


def testCachingOfClassPaths():
	testClassPathScan()
	time.sleep(2)
	testClassPathScan()
	touchFile("/Users/a/dev/sites/video.pixelami.com/src/haxe/org/pixelami/ui/UIComponent.hx")
	time.sleep(2)
	testClassPathScan()

def touchFile(filepath):
	atime = utime = time.time()
	os.utime(filepath,(atime, utime))

def runTests():
	
	assert(r)
	testCachingOfClassPaths()

if __name__ == '__main__':
	runTests()