# coding=utf-8
import serial
import sys
import m_db
import time
import logs

beginmsg = 'b'
countbegin = 10
endmsg = 'e'
selfaddr ='1'
maxwaittime = 1
maxrepeatcount = 1

logs.loglevel = m_db.params.loglevel()


class Chnl :
    def __init__(self):
        #self.port = serial.Serial(port=m_db.params.port(), baudrate=m_db.params.baudrate(),timeout=maxwaittime, rtscts=True,dsrdtr=True)
        self.port = serial.Serial(port=m_db.params.port(), baudrate=m_db.params.baudrate(),timeout=maxwaittime)

    def ReadResponce(self):
        state = 0
        msg =  ''
        while  state < 2 :
            c = self.port.read()
            logs.log.writelog('c = '+c, 3)
            if len(c) == 0 :
                msg=''
                state=2
            elif c == beginmsg :
                msg=''
                state = 1
            elif ('0' <= c <= '9' or c==':') and state == 1 :
                msg+=c
            elif c == endmsg and state == 1 :
                if msg.split(':')[0] == selfaddr :
                    state = 2
                else :
                    state = 0
                    msg =''
            #print msg
        if len(msg) > 0:
            logs.log.writelog('Получен ответ из канала '+msg,2)
        return msg



    def SendCmd(self,cmd):
        sndcount = 0
        sndstr = beginmsg*countbegin
        #for x in cmd :
        #    sndstr +=str(x) + str(':' if cmd.index(x)< (len(cmd)-2) else '')
        sndstr+=str(cmd)
        sndstr +=  endmsg
        sndstr = sndstr.replace(' ','').replace(',',':').replace('\'','').replace('[','').replace(']','')
        responce = ''

        while sndcount < maxrepeatcount and len(responce) == 0:
            self.port.flushInput()
            logs.log.writelog('Отправляется в канал команда '+sndstr,2)
            nwrite = self.port.write(sndstr)
            #print sndstr
            responce = self.ReadResponce()
            if len(responce) == 0 :
                logs.log.writelog('Нет ответа на '+str(cmd))
            sndcount+=1
        ret =  responce.split(':')
        return ret

    def Process(self):
        s = ''
        while s != 'close' :
            s= sys.stdin.readline().strip('\n')
            print s
            logs.log.writelog('Команда в канал '+s,1)
            if s != 'close' and s != 'end':
                cmd = s.replace('(','').replace(')','').replace('[','').replace(']','').split(',')
                res = self.SendCmd(cmd)
                try :

                    if len(res) >= 9:
                        m_db.mdb.SetSgValue(int(res[2]),int(res[8]))
                    else:
                        logs.log.writelog('Ошибка формата ответа от AVR '+ str(res.__str__())+'\n'+\
                            'Команда '+str(cmd))

                except :
                    se = sys.exc_info()
                    logs.log.writelog('Ошибка обработки ответа от AVR '+ str(res)+'\n'+\
                                  str(se[1])+'\n'+str(se[2].tb_frame.f_code))




chnl = Chnl()
chnl.Process()
chnl.port.close()
