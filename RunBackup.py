import os
import os.path
import sys
import argparse
import subprocess
import ConfigParser
import time

# Global vars
# **********************************
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BK_SRC_CFG = os.path.join(SCRIPT_DIR, "bk_src.cfg")

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

class BackupRunner(object):
    def __init__(self, srcCfgParser, destCfgParser):
        self.srcCfgParser = srcCfgParser
        self.destCfgParser = destCfgParser

    def __form_cmd_str__(self, src, dest):
        return "robocopy %s %s " % (src, dest)

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

    def Run(self):
        numOfSects = self.__chk_cfgs__()
        ind = 1
        for sec in self.destCfgParser.sections():
            src = self.srcCfgParser.get(sec, "src")
            dest = self.destCfgParser.get(sec, "dest")
            print "*" * 60
            print "* %d of %d" % (ind, numOfSects)
            print "* src = " + src
            print "* dst = " + dest
            time.sleep(0.5)
            __cmd__ = self.__form_cmd_str__(src, dest)
            print __cmd__
            p = subprocess.Popen(__cmd__, shell = True)
            p.communicate()
            if(p.returncode == 1):
                print "[OK] %s --> %s succeeded" % (src, dest)
            elif(p.returncode < 8):
                print "[OK] %s --> %s finished (robocopy returned %d)" % (src, dest, p.returncode)
            else:
                print "[ERROR] Failed %s --> %s (robocopy returned %d)" % (src, dest, p.returncode)
                print "[ERROR] Backup terminated with error"
                return
            ind += 1

# Main
# **********************************
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description = 'Run backups according to config file (%s)' % BK_SRC_CFG)
    argParser.add_argument('--dest', action = 'store', required = True)
    args = argParser.parse_args()

    srcCfgParser = ReadCfg(BK_SRC_CFG)
    destCfgParser = ReadCfg(os.path.join(SCRIPT_DIR, "bk_dest_%s.cfg" % args.dest))

    bkRunner = BackupRunner(srcCfgParser, destCfgParser)
    try:
        bkRunner.Run()
    except ValueError, ve:
        print '[ERROR] ' + ve.message
        sys.exit(1)
