import os
import re
import subprocess
from subprocess import Popen, PIPE

#compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)
#compactFunc = re.compile("\(.*\)")
#compactProp = re.compile(":.*\.([a-z_0-9]+)", re.I)
#spaceChars = re.compile("\s")
#wordChars = re.compile("[a-z0-9._]", re.I)

libLine = re.compile("([^:]*):[^\[]*\[(dev\:)?(.*)\]")
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

try:
    STARTUP_INFO = subprocess.STARTUPINFO()
    STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    STARTUP_INFO.wShowWindow = subprocess.SW_HIDE
except (AttributeError):
	STARTUP_INFO = None

def runcmd( args, input=None ):
	try:
		p = Popen(args, stdout=PIPE, stderr=PIPE, stdin=PIPE, startupinfo=STARTUP_INFO)
		if isinstance(input, unicode):
			input = input.encode('utf-8')
		out, err = p.communicate(input=input)
		return (out.decode('utf-8') if out else '', err.decode('utf-8') if err else '')
	except (OSError, ValueError) as e:
		err = u'Error while running %s: %s' % (args[0], e)
		return ("", err)


class ParamInfo:
	_name = None
	_type = None
	_defaultValue = None



class MethodInfo:
	_name = None
	_params = None
	_returnType = None
	_span = None

	def __init__(self,sourceInfo):
		src = self.sourceInfo.read()
		self._buildMethodInfo(src)

	def _buildMethodInfo(self,src):
		_params = []
		params = functionParamPattern.finditer(src)
		for parameter in params:
			cleanedParam = paramDefaultPattern.sub("",parameter)
			paramsList = cleanedParam.split(",")
			for param in paramsList:
				v = None
				t = None
				a = param.lstrip();
				if a.startswith("?"):
					a = a[1:]
				
				idx = a.find(":") 
				if idx > -1:
					a = a[0:idx]
					t = a[idx+1:]

				idx = a.find("=")
				if idx > -1:
					a = a[0:idx]
					v = a[idx+1:]


				a = a.strip()

				p = ParamInfo()
				p._name = a
				p._type = t
				p._defaultValue = v

				_params.append(p)
		
			

	def getParams():
		return _params

	def getParamsOrderedByType(self,type):
		sorted(_params, lambda item: item.type)
		return _params



class TypeInfo:

	_name = None
	_type = None
	_param = None
	_sourceInfo = None
	_variables = None
	_methods = None
	_span = None
	_inheritenceChain = None

	def __init__(self,sourceInfo):
		self._sourceInfo = sourceInfo

	def getSourceInfo(self):
		return self._sourceInfo

	def getType(self):
		return self._type

	def getName(self):
		return self._name

	def getVariables(self):
		if self._variables is None:
			self._buildTypeInfo()
		return self._variables

	def getMethods(self):
		if self._methods is None:
			self._buildTypeInfo()
		return self._methods

	def _buildTypeInfo(self):
		src = self.sourceInfo.read()
		self._variables = variablePattern.findall(src)
		self._methods = functionPattern.finditer(src)



class SourceInfo:
	
	_types = None
	_filepath = None
	_package = ""
	_cachedSource = ""

	def __init__(self,filepath):
		self._filepath = filepath

	def getVariables(self):
		return self._variables

	def getTypes(self):
		return self._types

	def getPackage(self):
		return self._package

	def getTypeInfo(self):
		types = []

		for m in self._types:
			defType, name, tParam = m.groups()
			typeInfo = TypeInfo(self)
			typeInfo._name = name
			typeInfo._type = defType
			typeInfo._param = tParam
			typeInfo._span = m.span()
			types.append( typeInfo )

		return types

	def read(self):
		if _cachedSource is not "":
			_cachedSource = resolver.getSourceFromFile( self.sourceInfo._filepath )
		return _cachedSource

	def clearCache(self):
		_cachedSource = ""

class _TypeDeclarationCache():
	
	declarations = None

	def __init__(self):
		self.declarations = {}

	def put(self, declaration, value):
		self.declarations[declaration] = value

	def get(self, declaration):
		if self.declarations.has_key(declaration):
			return self.declarations[declaration]


class _TypeDeclarationResolver():

	typeDeclarations = None
	fileModificationTimeTable = None
	cache = None
	sources = None
	
	def __init__(self):

		self.cache = _TypeDeclarationCache()
		self.fileModificationTimeTable = {}
		self.typeDeclarations = []

	
	def getSourcesInClassPath(self,classpath):
		
		self.sources = []
		for path, dirs, files in os.walk(classpath):
			for filename in files:
				if os.path.splitext(filename)[1] != ".hx":
					continue
				self.sources.append(os.path.join(path,filename))
		return self.sources


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
			#return self.cache.get(filepath)

		src = self.getSourceFromFile(filepath)

		info = SourceInfo(filepath)

		info._package = self.getPackageFromSource(src)
		
		info._types = typeDeclarationPattern.finditer(src)
		
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
		returns contents of a file as a string
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


class HaxeLib :

	available = {}
	basePath = None
	
	def __init__( self , name , dev , version ):
 		self.name = name
 		self.dev = dev
 		self.version = version
		self.classes = None
		self.packages = None
 
 		if self.dev :
 			self.path = self.version
 			self.version = "dev"
 		else : 
 			self.path = os.path.join( HaxeLib.basePath , self.name , ",".join(self.version.split(".")) )
 
 		#print(self.name + " => " + self.path)

	def extract_types( self ):
		if self.dev is True or ( self.classes is None and self.packages is None ):
			self.classes = resolver.getTypeDeclarationsInClassPath(self.path)
		
		return self.classes

	@staticmethod
	def get( name ) :
		if( name in HaxeLib.available.keys()):
			return HaxeLib.available[name]
		else :
			sublime.status_message( "Haxelib : "+ name +" project not installed" )
			return None

	@staticmethod
	def get_completions() :
		comps = []
		for l in HaxeLib.available :
			lib = HaxeLib.available[l]
			comps.append( ( lib.name + " [" + lib.version + "]" , lib.name ) )

		return comps

	@staticmethod
	def scan() :
		hlout, hlerr = runcmd( ["haxelib" , "config" ] )
		HaxeLib.basePath = hlout.strip()

		HaxeLib.available = {}

		hlout, hlerr = runcmd( ["haxelib" , "list" ] )

		for l in hlout.split("\n") :
			found = libLine.match( l )
			if found is not None :
				name, dev, version = found.groups()
				lib = HaxeLib( name , dev is not None , version )

				HaxeLib.available[ name ] = lib





class HaxeLibResolver:

	installedLibs = None

	def __init__(self):
		self.installedLibs = []


	def readInstalledLibs(self):
		HaxeLib.scan()
		for a in HaxeLib.available:
			//print a
			//print HaxeLib.available[a].extract_types()
			pass





resolver = _TypeDeclarationResolver()