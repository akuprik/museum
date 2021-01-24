__author__ = 'kupr'
import subprocess
import os
import time


class Player :
    def __init__(self,asopen,asclose):
        self.sopen = asopen
        self.sclose = asclose
        self.p = None

    def playFile(self,afilename):
        s=str(self.sopen+' '+afilename).rsplit(' ')

        print s
        fp = subprocess.Popen(s)
        if self.p != None :
            time.sleep(0.5)
            print self.p.pid
            self.p.terminate()
        self.p = fp
        print self.p.pid




    def stopPlay(self):
        if self.p != None:
            self.p.kill()
        s = 'ps  -C "'+self.sclose+'" -o pid,command | grep '+self.sclose
        #print s
        t = os.popen(s).read()
        try:
            #print t
            pidlist = t.split('\n')
            for x in pidlist:
                pid = x.strip('\n').split()[0]
                t = os.popen('kill -9 '+pid).read()
        except :
            pass





