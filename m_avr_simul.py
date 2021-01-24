# coding=utf-8
import serial
#import m_db

beginmsg = 'b'
countbegin = 10
endmsg = 'e'
selfaddr ='1'
maxwaittime = 1
maxrepeatcount = 2



class Chnl :
    def __init__(self):
        #self.port = serial.Serial(port='ttyc', baudrate=9600, rtscts=True,dsrdtr=True)
        self.port = serial.Serial(port='ttyc', baudrate=9600)

    def ReadResponce(self):
        state = 0
        msg =  ''
        while  state < 2 :
            c = self.port.read()
            if len(c) == 0 :
                msg=''
                state=2
            elif c == beginmsg :
                msg=''
                state = 1
            elif ('0' <= c <= '9' or c==':') and state == 1 :
                msg+=c
            elif c == endmsg and state == 1 :
                state = 2
        return msg


def GetTestValue(asgid):
    try :
        f = file('sgtest.txt','r')
        l = f.readline().strip('\n').split(',')
        print l
        ret = int(l[1]) if int(l[0])== int(asgid) else None
        f.close()
    except :
        ret = None
        print 'error'
    return ret



ch = Chnl()
while True :
    cmd = ch.ReadResponce().split(':')
    print 'Rcv> '+ str(cmd)
    if len(cmd)>7 :
        if int(cmd[1])==0:
            v=GetTestValue(cmd[2])
            cmd[8]=v if v != None else cmd[8]
        cmd[0]= selfaddr

        sndstr = beginmsg*countbegin
        sndstr += str(cmd).replace(' ','').replace(',',':').replace('\'','').replace('[','').replace(']','')
        sndstr += endmsg+'\n'
        print sndstr
        ch.port.writelines(sndstr)

ch.port.close()