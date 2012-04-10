import os
import re

#compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)
#compactFunc = re.compile("\(.*\)")
#compactProp = re.compile(":.*\.([a-z_0-9]+)", re.I)
#spaceChars = re.compile("\s")
#wordChars = re.compile("[a-z0-9._]", re.I)
importLine = re.compile("^([ \t]*)import\s+([a-z0-9._]+);", re.I | re.M)
packageLine = re.compile("package\s*([a-z0-9\.]*);", re.I)
#libLine = re.compile("([^:]*):[^\[]*\[(dev\:)?(.*)\]")
classpathLine = re.compile("Classpath : (.*)")
typeDecl = re.compile("(class|typedef|enum)\s+([A-Z][a-zA-Z0-9_]*)(<[a-zA-Z0-9_,]+>)?" , re.M )
#libFlag = re.compile("-lib\s+(.*?)")
#skippable = re.compile("^[a-zA-Z0-9_\s]*$")
#inAnonymous = re.compile("[{,]\s*([a-zA-Z0-9_\"\']+)\s*:\s*$" , re.M | re.U )
#comments = re.compile( "/\*(.*)\*/" , re.M )
#extractTag = re.compile("<([a-z0-9_-]+).*\s(name|main)=\"([a-z0-9_./-]+)\"", re.I)
variables = re.compile("var\s+([^:;\s]*)", re.I)
functions = re.compile("function\s+([^;\.\(\)\s]*)", re.I)
functionParams = re.compile("function\s+[a-zA-Z0-9_]+\s*\(([^\)]*)", re.M)
paramDefault = re.compile("(=\s*\"*[^\"]*\")", re.M)

class TypeDeclarationCache():
	
	declarations = None

	def __init__(self):
		self.declarations = {}

	def put(self, declaration, value):
		self.declarations[declaration] = value

	def get(self, declaration):
		if self.declarations.has_key(declaration):
			return self.declarations[declaration]


class TypeDeclarationResolver():

	typeDeclarations = None
	fileModificationTimeTable = None
	cache = None
	
	def __init__(self):
		self.cache = TypeDeclarationCache()
		self.fileModificationTimeTable = {}
		self.typeDeclarations = []

	def getTypeDeclarationsInClassPath(self,classpath):

		print "Getting declarations in classpath: %s" % classpath

		#re-initialize list
		self.typeDeclarations = []

		for path, dirs, files in os.walk(classpath):
			for filename in files:
				if os.path.splitext(filename)[1] != ".hx":
					continue
				
				filepath = os.path.join(path,filename)

				print "filepath: %s" % filepath
				modtime = os.path.getmtime(filepath)
				print "modtime: %d" % modtime
				useCache = False

				if self.fileModificationTimeTable.has_key(filepath):
					#check previous modtime
					previous_modtime = self.fileModificationTimeTable[filepath]
					#print "previous_modtime: %d" % previous_modtime
					if previous_modtime == modtime:
						useCache = True
				else:
					#cache current modtime
					self.fileModificationTimeTable[filepath] = modtime

				if useCache:
					print "using declaration cache"
					info = self.cache.get(filepath)
				else:
					info = self.getTypeDeclarationsInFile(filepath)
					self.cache.put(filepath, info)
				
				self.typeDeclarations.extend( info )
		
		return self.typeDeclarations

	def getTypeDeclarationsInFile(self,filepath):

		fh = open(filepath, "r")
		src = fh.read()
		fh.close()

		declarations = []
		package = self.getPackageFromSource(src)
		
		types = typeDecl.findall(src)
		print "types: %s " % types

		for decl in types:
			print decl
			declarations.append( (package , decl) )

		print declarations
		return declarations




	def getPackageFromSource(self,src):

		package = ""
		packageResult = packageLine.search(src)
		if packageResult:
			package = packageResult.group(1)
		return package
