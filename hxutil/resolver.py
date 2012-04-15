import os
import re

#compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)
#compactFunc = re.compile("\(.*\)")
#compactProp = re.compile(":.*\.([a-z_0-9]+)", re.I)
#spaceChars = re.compile("\s")
#wordChars = re.compile("[a-z0-9._]", re.I)

#libLine = re.compile("([^:]*):[^\[]*\[(dev\:)?(.*)\]")
#libFlag = re.compile("-lib\s+(.*?)")
#skippable = re.compile("^[a-zA-Z0-9_\s]*$")
#inAnonymous = re.compile("[{,]\s*([a-zA-Z0-9_\"\']+)\s*:\s*$" , re.M | re.U )
#comments = re.compile( "/\*(.*)\*/" , re.M )
#extractTag = re.compile("<([a-z0-9_-]+).*\s(name|main)=\"([a-z0-9_./-]+)\"", re.I)

importLinePattern = re.compile("^([ \t]*)import\s+([a-z0-9._]+);", re.I | re.M)
packageLinePattern = re.compile("package\s*([a-z0-9\.]*);", re.I)
classpathLinePattern = re.compile("Classpath : (.*)")
typeDeclarationPattern = re.compile("(class|typedef|enum)\s+([A-Z][a-zA-Z0-9_]*)(<[a-zA-Z0-9_,]+>)?" , re.M )
variablePattern = re.compile("var\s+([^:;\s]*)", re.I)
functionPattern = re.compile("function\s+([^;\.\(\)\s]*)", re.I)
functionParamPattern = re.compile("function\s+[a-zA-Z0-9_]+\s*\(([^\)]*)", re.M)
paramDefaultPattern = re.compile("(=\s*\"*[^\"]*\")", re.M)



class SourceInfo():
	
	_types = None
	_variables = None
	_filepath = None
	_package = ""

	def __init__(self,filepath):
		self._filepath = filepath

	def getVariables(self):
		return _variables

	def getTypes(self):
		return _types

	def getPackage(self):
		return _package

	def getTypeInfo(self):
		types = []
		for defType, name, tParam  in self._types:
			types.append( (self._package, defType, name, tParam) )
		return types



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

		#print "Getting declarations in classpath: %s" % classpath

		#re-initialize list
		self.typeDeclarations = []

		for path, dirs, files in os.walk(classpath):
			for filename in files:
				if os.path.splitext(filename)[1] != ".hx":
					continue
				
				filepath = os.path.join(path,filename)
				#print "filepath: %s" % filepath

				info = self.getTypeDeclarationsInFile(filepath)
				self.typeDeclarations.extend( info.getTypeInfo() )
		
		return self.typeDeclarations

	

	def getTypeDeclarationsInFile(self,filepath):

		"""
		returns a list of type declaration info from a hx file
		The file is scanned for type pattern matches and caches
		the result of the scan, using the filepath as the cache 
		key. If the file was not modified since last scan, then
		the previous cached scan is returned
		"""

		if not self.fileHasBeenModified(filepath):
			print("using cache")
			return self.cache.get(filepath)

		src = self.getSourceFromFile(filepath)

		info = SourceInfo(filepath)

		info._package = self.getPackageFromSource(src)
		
		info._types = typeDeclarationPattern.findall(src)

		self.cache.put(filepath, info)
		return info
	

	def getVarsFromSource(self,src):

		"""
		returns a list of vars found in given hx file
		"""

		variables = variablesPattern.findall(src)

		return variables



	def getPackageFromSource(self,src):
		
		"""
		returns the package from hx file
		"""

		package = ""
		packageResult = packageLinePattern.search(src)
		if packageResult:
			package = packageResult.group(1)
		return package

	

	def getSourceFromFile(self,filepath):
		
		"""
		returns contents of a file as  a string
		"""

		fh = open(filepath, "r")
		src = fh.read()
		fh.close()
		return src

	def fileHasBeenModified(self,filepath):

		modtime = os.path.getmtime(filepath)

		if self.fileModificationTimeTable.has_key(filepath):
			#check previous modtime
			previous_modtime = self.fileModificationTimeTable[filepath]
			#print "previous_modtime: %d" % previous_modtime
			if previous_modtime == modtime:
				return False
		else:
			#cache current modtime
			self.fileModificationTimeTable[filepath] = modtime
		return True

