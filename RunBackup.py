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
CFG_BASE = os.path.join(SCRIPT_DIR, 'config')
SRC_CFG = "src.cfg"

OS_OSX = "Darwin"
OS_WINDOWS = "Windows"

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
        elif(p.returncode < 8):
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
    else:
        raise Exception('OS not supported yet: neither OSX nor Windows') 

class BackupRunner(object):
    # syncContent: content to sync, should be the name as defined in cfg files.
    def __init__(self, srcCfgParser, destCfgParser, syncContent = None):
        self.srcCfgParser = srcCfgParser
        self.destCfgParser = destCfgParser
        self.syncContent = syncContent

    def __chk_cfgs__(self):
        ind = 0
        for sec in self.destCfgParser.sections():
            try:
                dest = self.destCfgParser.get(sec, "dest")
                if not dest:
                    raise ValueError("Invalid value in destCfg %s:%s" % (sec, "dest"))
            except ConfigParser.NoOptionError, exp:
                raise ValueError(exp._Error__message + " (destCfg)")
            
            try:
                src = self.srcCfgParser.get(sec, "src")
                if not src:
                    raise ValueError("Invalid value in srcCfg %s:%s" % (sec, "src"))
            except ConfigParser.NoSectionError, exp:
                raise ValueError(exp._Error__message + " (srcCfg)")
            except ConfigParser.NoOptionError, exp:
                raise ValueError(exp._Error__message + " (srcCfg)")
            ind += 1

        return ind
    
    def __mount_unc__(self):
        for cfg in [self.srcCfgParser, self.destCfgParser]:
            if(cfg.has_option('DEFAULT', 'unc.root')):
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
        numOfSects = self.__chk_cfgs__()
        self.__mount_unc__()
        ind = 1
        for sec in self.destCfgParser.sections():
            if self.syncContent and self.syncContent != sec:
                print "[%s] is not same as syncContent '%s', ignore it" % (sec, self.syncContent)
                continue
            
            src = self.srcCfgParser.get(sec, "src")
            dest = self.destCfgParser.get(sec, "dest")
            print "*" * 60
            print "* %d of %d" % (ind, numOfSects)
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

# Main
# **********************************
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description = 'Run backups according to config file (%s)' % SRC_CFG)
    argParser.add_argument('--cfg', action = 'store', required = True, help = 'config name under SCRIPT_DIR/config/')
    argParser.add_argument('--dest', action = 'store', required = True, help = 'destination name, as dest_sg3.cfg it is sg3')
    argParser.add_argument('--content', action = 'store', required = True, help = 'content to be backed-up, as \'photo\'')
    args = argParser.parse_args()

    cfgDir = os.path.join(CFG_BASE, args.cfg)
    if(os.path.isdir(cfgDir)):
        print "I will do backup for config under: %s" % cfgDir
    else:
        print "[ERROR] invalid config name: %s" % args.cfg
        sys.exit(1)

    srcCfgParser = ReadCfg(os.path.join(cfgDir, SRC_CFG))
    destCfgParser = ReadCfg(os.path.join(cfgDir, "dest_%s.cfg" % args.dest))

    bkRunner = BackupRunner(srcCfgParser, destCfgParser, args.content)
    try:
        bkRunner.Run()
    except ValueError, ve:
        print '[ERROR] ' + ve.message
        sys.exit(1)
