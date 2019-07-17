import subprocess
import platform,os
from xml.dom.minidom import parse
import xml.dom.minidom
import time

class XMLHandler:
    def __init__(self,filePath):
        # self.xmlDir = os.path.abspath("..") + os.path.sep + "mutator.xml"
        self.xmlDir = filePath
        self.androidProject = ""
        self.androidSourcePath = ""
        self.mutantFileDir= ""
        self.sourceDir = ""
        self.mutantApkDir = ""
        self.settings = {}

    def readXML(self):
        DOMTree = xml.dom.minidom.parse(self.xmlDir)
        Settings = DOMTree.documentElement
        Mutation = Settings.getElementsByTagName("Mutation")
        Directory = Mutation[0].getElementsByTagName("Directory")
        for directory in Directory:
            if directory.hasAttribute("name"):
                self.settings[directory.getAttribute("name")] = directory.childNodes[0].data
        Builder = Settings.getElementsByTagName("Builder")
        Directory = Builder[0].getElementsByTagName("Directory")
        for directory in Directory:
            if directory.hasAttribute("name"):
                self.settings[directory.getAttribute("name")] = directory.childNodes[0].data
        #print self.settings
        return self.settings

def subprocess_run(cmd):
    try:
        result = []
        proc = None
        if platform.system().upper() == "LINUX":
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
        elif platform.system().upper() == "WINDOWS":
            proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc is None:
            print "creating subprocess failed."
            return  result
        (stdout, stderr) = proc.communicate()
        #if stderr is not None:
        #    print stderr
        output = stdout.split(os.linesep)
        for line in output:
            tempLine = line.strip()
            if tempLine == '':
                continue
            result.append(tempLine)
        proc.terminate()
    except Exception as err:
        raise Exception("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))
    return result

def os_run(cmd):
    ret = os.popen(cmd)
    result = ret.read()
    ret.close()
    return result

def read_mutation_project():
    mutation_project = "./mutation_project.config"
    readFile = open(mutation_project, "r")
    vtLines = readFile.readlines()
    dProject = {}
    for line in vtLines:
        if line.strip().startswith("#") or line.strip() == "":
            continue
        dProject[line.strip()] = ""
    readFile.close()
    return dProject

project_xml_dir = "./project_xml"
project_xml_dir = os.path.abspath(project_xml_dir)
vtProject_xml = os.listdir(project_xml_dir)
dictProject = read_mutation_project()

def generateMutants():
    # generating mutants
    for xmlName in vtProject_xml:
        if not dictProject.has_key(xmlName.replace(".xml","")):
            continue
        settings = XMLHandler(project_xml_dir+os.sep+xmlName).readXML()
        print "Mutating "+settings["project_name"]+"..."
        cmd = "java -jar DroidMutator-1.2.jar project_config="+project_xml_dir+os.sep+xmlName
        print "Executing Cmd: "+cmd
        vtResult = subprocess_run(cmd)
        for line in vtResult:
            print line
            ## All files are handled. Execution Time:1.83s
            if str(line).startswith("All files are handled"):
                outputFileDir = settings["mutation_home"] + os.sep + "reports"
                if not os.path.exists(outputFileDir):
                    os.makedirs(outputFileDir)
                outputFile = open(outputFileDir + os.sep + settings["project_name"] + "_report.txt", "a")
                outputFile.write("----------------------------------------------------" + os.linesep)
                outputFile.write(
                    "Mutation output (" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "):" + os.linesep)
                outputFile.write("----------------------------------------------------" + os.linesep)
                outputFile.write("Mutation Time: " + line+ os.linesep)
                outputFile.write("----------------------------------------------------")
                outputFile.close()

def generateApk():
    # generating apk
    for xmlName in vtProject_xml:
        if not dictProject.has_key(xmlName.replace(".xml", "")):
            continue
        settings = XMLHandler(project_xml_dir + os.sep + xmlName).readXML()
        compileProjectPy = settings["mutation_home"] + os.sep + "builder" + os.sep + "compileAndroidPro.py"
        print "Compiling " + settings["project_name"] + "..."
        cmd = "python -u " + compileProjectPy + " " + project_xml_dir + os.sep + xmlName
        print "Executing Cmd: " + cmd
        try:
            ret = subprocess.check_call(cmd, shell=True)
            if ret == 0:
                print "Task completed..."
        except subprocess.CalledProcessError:
            print "Task failed..."
        #vtResult = subprocess_run(cmd)
        #for line in vtResult:
        #    print line

def filterApk():
    # filtering crash apk
    for xmlName in vtProject_xml:
        if not dictProject.has_key(xmlName.replace(".xml", "")):
            continue
        settings = XMLHandler(project_xml_dir + os.sep + xmlName).readXML()
        launchProjectPy = settings["mutation_home"] + os.sep + "launcher" + os.sep + "RunMutants.py"
        print "Launching " + settings["project_name"] + "..."
        cmd = "python -u " + launchProjectPy + " " + project_xml_dir + os.sep + xmlName
        print "Executing Cmd: "+cmd
        try:
            ret = subprocess.check_call(cmd, shell=True)
            if ret == 0:
                print "Task completed..."
        except subprocess.CalledProcessError:
            print "Task failed..."
            vtResult = subprocess_run(cmd)
            for line in vtResult:
                print line

def Main():
    generateMutants()
    generateApk()
    #filterApk()

if __name__ == "__main__":
    Main()
