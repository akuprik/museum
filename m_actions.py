# coding=utf-8
import time
import os
import m_db
import logs
import m_communicate
import m_player

cmd_Pool = 0
cmd_OnOff = 1
cmd_SetValue = 2
pr_Ok = 0
pr_Finish = 1

logs.log.loglevel = m_db.params.loglevel()

pcom = m_communicate.Communicator()

player = m_player.Player(m_db.params.playfilecmd(),m_db.params.stopfilecmd())




class Sg:
    def __init__(self, aaction, aparams):
        self.action = aaction
        self.sgid = aparams[11]
        self.value4set = aparams[12]
        self.sgtype = aparams[13]
        self.sgname = str(aparams[15].encode('utf8') if aparams[15] != None else '' )
        self.addr = aparams[16]
        self.pin1 = aparams[17] if aparams[17] != None else 0
        self.pin2 = aparams[18] if aparams[18] != None else 0
        self.pin3 = aparams[19] if aparams[19] != None else 0
        self.pin4 = aparams[20] if aparams[20] != None else 0
        self.lastvalue = 0
        self.valuetime = 0.0
        logs.log.writelog('Cоздание сигнала id_sg='+str(self.sgid)+' '+self.sgname,1)

    def GetCmd(self,cmd,value):
        ret = list()
        ret.append(self.addr)
        ret.append(cmd)
        ret.append(self.sgid)
        ret.append(self.sgtype)
        ret.append(self.pin1)
        ret.append(self.pin2)
        ret.append(self.pin3)
        ret.append(self.pin4)
        ret.append(self.value4set)
        return ret


class Sgs(list) :
    def __init__(self,aaction):
        self.action = aaction
        sglist  = m_db.mdb.GetActionParams(self.action.actionid)
        for x in sglist._rows:
            self.append(Sg(self.action,x))

class Action:
    def __init__(self,astate,aaction):
        self.state = astate
        self.actionid = aaction[0]
        self.order=aaction[2]
        self.actiontype = aaction[3]
        self.actionname = str(aaction[4].encode('utf8') if aaction[4] != None else '')
        self.starttype = aaction[5]
        self.starttimefrom = aaction[6]
        self.starttime = 0.0
        self.param = aaction[7]
        self.position = aaction[8]
        logs.log.writelog('Cозданние действия '+self.actionname+'('+str(self.actionid)+') для state='+str(self.state.stateid),1)
        self.sgs = Sgs(self)


    def Reset(self):
        self.starttime = 0.0




    def ActionRun(self):
        #print 'run action='+str(self.actionid)+'  '+str(self.actionname)
        ret = pr_Ok
        self.starttime = time.time()
        logs.log.writelog('Запуск акции (state:'+str(self.state.stateid)+' action:'+str(self.actionid)+') '+\
                            'starttime = '+str(self.starttime),1)
        if self.actiontype == 1 : #Установить Вкл.Выкл (1/0)
            logs.log.writelog('Установить Вкл/Выкл (state='+str(self.state.stateid)+\
                                  '  actionid='+str(self.actionid)+'  param='+str(self.param)+')',1)
            try :
                val = int(self.param)
            except ValueError:
                logs.log.writelog('Ошибка параметра акции (state='+str(self.state.stateid)+\
                                  '  actionid='+str(self.actionid)+'  param='+str(self.param)+')')
                val = 0
            cmd = ''
            for x in self.sgs :
                cmd += str(x.GetCmd(cmd_OnOff,val))+'\n'
            pcom.Send(cmd)

        elif self.actiontype ==2 : #Установить Уровень
            logs.log.writelog('Установить уровень (state='+str(self.state.stateid)+\
                                  '  actionid='+str(self.actionid)+'  param='+str(self.param)+')',1)
            val = 0
            cmd = ''
            for x in self.sgs :
                cmd += str(x.GetCmd(cmd_SetValue,val))+'\n'
            pcom.Send(cmd)

        elif self.actiontype ==3 : #Проиграть файл
            logs.log.writelog('Проиграть файл (state='+str(self.state.stateid)+\
                                  '  actionid='+str(self.actionid)+'  param='+str(self.param)+')',1)
            player.playFile(self.actionname)

        elif self.actiontype ==4 : #Установить произгование файла
            logs.log.writelog('Остановить проигрывание файла (state='+str(self.state.stateid)+\
                                  '  actionid='+str(self.actionid)+'  param='+str(self.param)+')',1)
            player.stopPlay()

        elif self.actiontype == 100 : #Завершить состояние
            #if (self.state.stateid == 1) and  (len(self.state.actions.SearchNotRun()) < 1):
            #    logs.log.writelog('Окончние режима (state='+str(self.state.stateid)+\
            #                          '  actionid='+str(self.actionid)+'  param='+str(self.param)+')',1)
            #    ret = pr_Finish
            #else :
            #    #self.state.actions.Reset()
            #    ret = pr_Finish
            self.state.Reset()
            self.state.states.current = int(self.param) -1
            ret = pr_Finish
        return ret;


    def Process(self):
        dt = 0
        ret = pr_Ok
        if self.starttime == 0.0 :
            if self.starttype == 1 : # От начала режима
                dt =  (time.time() - self.state.starttime) * 1000
                #print 'time='+str(time.time())+' atime='+str(self.state.starttime)+'   state='+str(self.state.stateid)+'  action='+str(self.actionid)+'  dt='+str(dt)+'  st='+str(self.starttimefrom)
            elif self.starttype == 2: #От датчика движения
                dt = (time.time()-float(m_db.mdb.CheckMoveSensor())) * 1000
            elif self.starttype == 3: #От отсутствия движения
                dt = (time.time() - float(m_db.mdb.CheckNoMoveSensor())) * 1000

            elif self.starttype == 4: #От предыдущего шага c id_action
                pa = self.state.actions.GetAction(int(self.param))
                if pa != None :
                    if  pa.starttime > 0:
                        dt = (time.time() - pa.starttime) * 1000
                else :
                    logs.log.writelog('Ошибка параметра. '+self.actionname+'(actionid='+str(self.actionid)+') Нет шага '+str(self.param))
            if dt > self.starttimefrom :
                #print 'run action='+str(self.actionid)+'  '+str(self.actionname)
                ret = self.ActionRun()
        return ret


class Actions(list) :

    def __init__(self,astate):
        self.state = astate
        actionlist = m_db.mdb.GetActions(self.state.stateid)
        logs.log.writelog('Создание списка действий для state='+str(self.state.stateid),1)
        for x in actionlist._rows:
            self.append(Action(self.state,x))
        logs.log.writelog('Список действий для state='+str(self.state.stateid)+' создан',1)

    def Reset(self):
        for x in self :
            x.Reset()

    def Process(self):
        ret = pr_Finish
        for x in self:
            ret = x.Process()
            if ret == pr_Finish:
                return ret
        return ret

    def GetPrevious(self,aaction):
        try:
            i = self.index(aaction)
        except:
            i=0
        i = i - (1 if i>0 else 0)
        return self[i]

    def GetAction(self,aactionid):
        ret = None
        i = 0
        while ret == None and i < len(self) :
            ret = self[i] if self[i].actionid == aactionid else None
            i+=1
        return ret

    def FindByManualOrder(self,amanualorder):
        ret = list()
        i = 0
        while i<len(self) :
            if self[i].position == amanualorder :
                ret.append(self[i])
            i+=1
        return ret if len(ret)>0 else None

    def SearchNotRun(self):
        l = list()
        for x in self:
            if not(x.starttime > 0):
                l.append(x)

        #print 'len='+str(len(l))
        return l

class State:
    def __init__(self,astateid,astates):
        self.stateid =  astateid
        self.states = astates
        logs.log.writelog('Создание state='+str(self.stateid),1)
        self.actions = Actions(self)
        self.starttime = 0.0
        logs.log.writelog('Создан state='+str(self.stateid),1)

    def Reset(self):
        self.starttime = 0.0
        self.actions.Reset()

    def Process(self):
        if self.starttime == 0:
            self.starttime = time.time()
            logs.log.writelog('Запуск режима '+str(self.stateid) + '  starttime='+str(self.starttime), 1)
        return self.actions.Process()


class States(list) :
    def __init__(self):
        statelist = m_db.mdb.GetStates()
        self.current = 0
        self.isAuto = True
        self.Position = 0
        self.PositionDone = True
        self.CommandTime = 0.0
        logs.log.writelog('Создание списка состояний ',1)
        for x in statelist._rows:
            self.append(State(statelist.FieldValue(x,'id_statetype'),self))
        self.Reset()
        logs.log.writelog('Список состояний создан',1)


    def FindActionByManualOrder(self,amanualorder):
        ret = None
        i = 0
        while i<len(self) and ret == None :
            ret = self[i].actions.FindByManualOrder(amanualorder)
            i+=1
        return ret

    def GetMaxManualOrder(self):
        ret = 0;
        for st in self:
            for a in st.actions:
                if a.position > ret:
                    ret = a.position
        return ret

    def CurrentState(self):
        return self[self.current]

    def NextState(self):
        #self.CurrentState().Reset();
        self.current = (self.current if self.current < (len(self)-1) else -1) + 1
        return self.CurrentState()

    def FirstState(self):
        self.current = 0
        return self.CurrentState()


    def Reset(self):
        for x in self:
            x.Reset()

    def RunPosition(self):
        ret = False
        maxPosition = self.GetMaxManualOrder()
        #print 'maxPosition='+str(maxPosition)
        while not ret and self.Position <= maxPosition:
            #print 'Position = '+str(self.Position)
            actions = self.FindActionByManualOrder(self.Position)
            #print str(actions)
            if actions != None  :

                ret = True
                for x in actions:
                    if  x.starttime == 0.0 :
                        x.ActionRun()
            else :
                self.Position += 1
                if self.Position > maxPosition :
                    self.ret = True

        return ret






    def RunProcess(self):
        if self.isAuto :
            cs = self.CurrentState()
            res = cs.Process()
            #print self.current;
            if res == pr_Finish :
                logs.log.writelog('Переход на сл. режим',1)
                self.NextState()
        else :
            self.PositionDone = self.RunPosition()



    def PoolSensors(self):
        if (not((self.CurrentState().stateid == 1) and (len(self.CurrentState().actions.SearchNotRun()) > 1))) or not self.isAuto:
            sl = m_db.mdb.GetSensors()
            cmd = ''
            for sg in sl._rows :
                if self.isAuto or (not self.isAuto and sl.FieldValue(sg,'sgtype') != 1):
                    cmd += str(sl.FieldValue(sg,'addr'))+','
                    cmd += str(cmd_Pool)+','
                    cmd += str(sl.FieldValue(sg,'id_sg'))+','
                    cmd += '1,'
                    cmd += str(sl.FieldValue(sg,'pin1'))+','
                    cmd += str(sl.FieldValue(sg,'pin2'))+','
                    cmd += str(sl.FieldValue(sg,'pin3'))+','
                    cmd += str(sl.FieldValue(sg,'pin4'))+','
                    cmd += '0'+'\n'
            pcom.Send(cmd)





    def SetManualState(self):
        self.isAuto = False
        self.Position = 1
        self.PositionDone = False
        for x in self[0].actions :
            if x.actiontype != 3 and x.actiontype != 100 :
                x.ActionRun()
        self.Reset()

    def SetAutoState(self):
        self.isAuto = True
        self.current = 0;
        self.Reset();




    def TestCommand(self):
        cmdsg = m_db.mdb.CheckCommand()

        if cmdsg != None :
            if float(cmdsg[9]) > self.CommandTime :
                self.CommandTime = float(cmdsg[9])
                cmd = int(cmdsg[1])
                #print 'cmd='+str(cmd)
                if cmd == 5 :
                    logs.log.writelog('Нажата кнопка A брелка (команда '+str(cmd)+')',1)
                    #print 'button A'
                    self.SetManualState()

                elif cmd == 6:
                    #print 'button B'
                    logs.log.writelog('Нажата кнопка B брелка (команда '+str(cmd)+')',1)
                    self.SetAutoState()

                elif cmd == 7:
                    #print 'button C'
                    logs.log.writelog('Нажата кнопка С брелка (команда '+str(cmd)+')',1)
                    self.Position +=1
                    self.PositionDone = False

                elif cmd == 8:
                    logs.log.writelog('Нажата кнопка D брелка (команда '+str(cmd)+')',1)
                    #print 'button D'
                    #self.Position -=1
                    #if self.Position <= 0 :
                    #    self.Position = 1
                    #self.PositionDone = False

