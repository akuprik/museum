# coding=utf-8
import subprocess
import os
import logs


class Communicator :
    def __init__(self):
        t = os.popen('ps  -C "python" -o pid,command | grep m_chnl').read()
        try:
            pid = t.split()[0]
            t = os.popen('kill -9 '+pid).read()
            logs.log.writelog('Удаление m_chnl (pid '+pid+'  '+t+')',1)
        except :
            pass
        self.p = subprocess.Popen(['python','-u','./m_chnl.py'],stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def Send(self,cmd):
        self.p.stdout.flush()
        self.p.stdin.writelines(cmd+'end\n')
        s = ''
        while s.strip('\n') <> 'end':
            s=self.p.stdout.readline()

            #print s


    def Close(self):
        self.p.stdin.write('close\n')


