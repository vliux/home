import os
import os.path
import re
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

EXCLUDE_DIRS = ["$RECYCLE.BIN", "System Volume Information", ".Trashes", ".Spotlight-V100"]

# Classes & functions
# **********************************
def ReadCfg(cfgFile):
    srcCfgParser = ConfigParser.ConfigParser()
    print "Read cfg %s" % cfgFile
    files = srcCfgParser.read([cfgFile])
    if not files:
        raise Exception('Unable to read backup config file at %s' % cfgFile)
    else:
        return srcCfgParser

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

class BackupRunner(object):
    # syncContent: content to sync, should be the name as defined in cfg files.
    def __init__(self, cfgParser, srcPathRoot, destPathRoot):
        self.cfgParser = cfgParser
        print cfgParser
        self.srcPathRoot = srcPathRoot
        self.destPathRoot = destPathRoot
        self.srcPathReExpList = self.__compile_src_path_re_list__()
    
    def __compile_src_path_re_list__(self):
        srcPathReExpList = []
        for sect in self.cfgParser.sections():
            srcPathReExp = self.cfgParser.get(sect, "src")
            srcPathReExpList.append(re.compile(srcPathReExp))
        return srcPathReExpList

    def __mount_unc_if_needed__(self):
            if(self.cfgParser.has_option('DEFAULT', 'unc.root')):
                root = cfg.get('DEFAULT', 'unc.root')
                usr = cfg.get('DEFAULT', 'unc.usr')
                passwd = cfg.get('DEFAULT', 'unc.passwd')
                print "Mount UNC share %s ..." % root
                __cmd__ = "net use %s %s /USER:%s /PERSISTENT:YES" % (root, passwd, usr)
                print __cmd__
                p = subprocess.Popen(__cmd__, shell = True)
                p.communicate()
                print "net-use returned %d" % p.returncode
    
    def Run(self):
        self.__mount_unc_if_needed__()
        ind = 1
        for fd in os.listdir(self.srcPathRoot):
            if fd in EXCLUDE_DIRS:
                print "%s in EXCLUDE list, skipping ..." % fd
                continue
            elif fd == CFG_FILE_NAME:
                continue
            else:
                for srcPathReExp in self.srcPathReExpList:
                    print srcPathReExp
                    if srcPathReExp.match(fd):           
                        src = os.path.join(self.srcPathRoot, fd)
                        dest = os.path.join(self.destPathRoot, fd)
                        print "*" * 60
                        print "* NO. %d" % (ind)
                        print "* src = " + src
                        print "* dst = " + dest
                        time.sleep(0.5)
                        __cmd__ = getOsCmd(src, dest)
                        print __cmd__
                        p = subprocess.Popen(__cmd__, shell = True)
                        p.communicate()
                        if(checkOsCmdRetCode(p.returncode, src, dest) == 0):
                            ind += 1
                            continue
                        else:
                            return
                print "%s not matched by backup rules, skipping ..." % fd
                continue

# Main
# **********************************
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description = 'Run backups according to config file (%s) in the source path/device' % CFG_FILE_NAME)
    argParser.add_argument('-s', '--src', action = 'store', required = True, help = 'Root path of the source folder or device')
    argParser.add_argument('-d', '--dst', action = 'store', required = True, help = 'Root path of the target backup folder or device')
    args = argParser.parse_args()
    
    cfgParser = ReadCfg(os.path.join(args.src, CFG_FILE_NAME))
    bkRunner = BackupRunner(cfgParser, args.src, args.dst)
    try:
        bkRunner.Run()
    except ValueError, ve:
        print '[ERROR] ' + ve.message
        sys.exit(1)
