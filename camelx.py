import os
import os.path
import sys
import argparse
import subprocess
import ConfigParser
import time
import platform

# Global vars
# **********************************
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
CFG_FILE_NAME = "CAMELX.cfg"

OS_OSX = "Darwin"
OS_WINDOWS = "Windows"

CFG_SECTION_DEFAULT = "DEFAULT"
CFG_KEY_SRC_ROOT = "src.root"
CFG_KEY_DEST_ROOT = "dest.root"
CFG_KEY_DIR = "dir"


# Config classes
# **********************************
class CamelxConfig:
    def __init__(self, srcPath, destPath):
        self.srcPath = srcPath
        self.destPath = destPath


class CamelxConfigParser(object):
    def __init__(self, cfgFile):
        self.cfgFile = cfgFile
        self.cfgParser = self.readCfg()

    def readCfg(self):
        srcCfgParser = ConfigParser.ConfigParser()
        print "Read cfg %s" % self.cfgFile
        files = srcCfgParser.read([self.cfgFile])
        if not files:
            raise Exception('Unable to read backup config file at %s' % self.cfgFile)
        else:
            return srcCfgParser

    def parse(self):
        srcRoot = self.cfgParser.get(CFG_SECTION_DEFAULT, CFG_KEY_SRC_ROOT)
        destRoot = self.cfgParser.get(CFG_SECTION_DEFAULT, CFG_KEY_DEST_ROOT)
        results = []
        for section in self.cfgParser.sections():
            dirName = self.checkNonNullValue(CFG_KEY_DIR, self.cfgParser.get(section, CFG_KEY_DIR))
            src = os.path.join(srcRoot, dirName)
            dest = os.path.join(destRoot, dirName)
            results.append(CamelxConfig(src, dest))
        return results

    def checkNonNullValue(self, key, value):
        if not value:
            raise Exception("Undefined config in file %s, key=%s" % (self.cfgFile, key))
        else:
            return value


# Utility functions
# **********************************
def getOsCmd(src, dest):
    currOs = platform.system()
    if(OS_WINDOWS == currOs):
        return "robocopy \"%s\" \"%s\" /MIR /FP" % (src, dest)
    elif(OS_OSX == currOs):
        return "rsync -varH --delete --progress %s %s" % (src, dest)
    else:
        raise Exception('OS not supported yet: neither OSX nor Windows')

def checkOsCmdRetCode(returncode, src, dest):
    currOs = platform.system()
    if(OS_WINDOWS == currOs):
        if(returncode == 1):
            print "[OK] %s --> %s succeeded" % (src, dest)
            return 0
        elif(returncode < 8):
            print "[OK] %s --> %s finished (robocopy returned %d)" % (src, dest, returncode)
            return 0
        else:
            print "[ERROR] Failed %s --> %s (robocopy returned %d)" % (src, dest, returncode)
            print "[ERROR] Backup terminated with error"
            return 1
    elif(OS_OSX == currOs):
        if(returncode == 0):
            print "[OK] %s --> %s succeeded" % (src, dest)
            return 0
        else:
            print "[ERROR] Failed %s --> %s (rsync returned %d)" % (src, dest, returncode)
            return 1
    else:
        raise Exception('OS not supported yet: neither OSX nor Windows') 


# Backup runner class
# **********************************
class BackupRunner(object):
    def __init__(self, camelxConfigParser):
        self.camelxConfigParser = camelxConfigParser

    #def __mount_unc_if_needed__(self):
    #        if(self.cfgParser.has_option('DEFAULT', 'unc.root')):
    #            root = cfg.get('DEFAULT', 'unc.root')
    #            usr = cfg.get('DEFAULT', 'unc.usr')
    #            passwd = cfg.get('DEFAULT', 'unc.passwd')
    #            print "Mount UNC share %s ..." % root
    #            __cmd__ = "net use %s %s /USER:%s /PERSISTENT:YES" % (root, passwd, usr)
    #            print __cmd__
    #            p = subprocess.Popen(__cmd__, shell = True)
    #            p.communicate()
    #            print "net-use returned %d" % p.returncode
    
    def Run(self):
        #self.__mount_unc_if_needed__()
        camelxConfigList = self.camelxConfigParser.parse()
        ind = 1
        for camelxConfig in camelxConfigList:
            print "*" * 60
            print "* NO. %d" % (ind)
            print "* src = " + camelxConfig.srcPath
            print "* dst = " + camelxConfig.destPath
            time.sleep(0.5)
            __cmd__ = getOsCmd(camelxConfig.srcPath, camelxConfig.destPath)
            print __cmd__
            p = subprocess.Popen(__cmd__, shell = True)
            p.communicate()
            if(checkOsCmdRetCode(p.returncode, camelxConfig.srcPath, camelxConfig.destPath) == 0):
                ind += 1
                continue
            else:
                return False
        assert ind == len(camelxConfigList) + 1
        return True


# Main
# **********************************
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description = 'Run backups according to config file (%s) in the target path' % CFG_FILE_NAME)
    argParser.add_argument('-c', '--cfg', action = 'store', required = True, help = 'Path of dir containing the config file %s' % CFG_FILE_NAME)
    args = argParser.parse_args()
    
    camelxConfigParser = CamelxConfigParser(os.path.join(args.cfg, CFG_FILE_NAME))
    bkRunner = BackupRunner(camelxConfigParser)
    try:
        bkRunner.Run()
    except ValueError, ve:
        print '[ERROR] ' + ve.message
        sys.exit(1)
