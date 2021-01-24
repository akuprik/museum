# coding=utf-8
import sys
import sqlite3 as sqlt
import time
import MyrecordSet
import logs

dbname = 'museumdb.sqlite'


class MuseumDB :

    def __init__(self):
        self.con = sqlt.connect(dbname)
        self.cur = self.con.cursor()

    def GetParams(self):
        self.cur.execute('select * from params')
        return MyrecordSet.MyRecordset(self.cur.fetchall(),self.cur.description)

    def GetActionParams(self, actionid = 0):
        self.cur.execute('select * from vstates where ' +\
                         'id_action = '+str(actionid if actionid != 0 else  ' action ')+' order by state,orderinstate,id_sg')
        return MyrecordSet.MyRecordset(self.cur.fetchall(),self.cur.description)

    def GetActions(self,stateid):
        self.cur.execute('select * from actions where state = '+str(stateid)+' order by state, orderinstate')
        return MyrecordSet.MyRecordset(self.cur.fetchall(),self.cur.description)

    def GetStates(self):
        self.cur.execute('select * from statetypes order by id_statetype')
        return MyrecordSet.MyRecordset(self.cur.fetchall(),self.cur.description)

    def CheckMoveSensor(self):
        ctime = time.time()
        self.cur.execute('update sgs set value = 0, valuetime = ? where sgtype = 1 and value = 1 and ? - valuetime > 1*60*60 ',\
                         [ctime,ctime])
        self.con.commit()
        self.cur.execute('select min(valuetime) mintime from sgs where sgtype = 1 and value = 1')
        ls = self.cur.fetchall()
        t = ls[0][0]
        return t if t != None else ctime+10


    def CheckNoMoveSensor(self):
        ctime = time.time()
        self.cur.execute('update sgs set value = 0, valuetime = ? where sgtype = 1 and value = 1 and  ? - valuetime > 1*60*60 ',\
                         [ctime,ctime])
        self.con.commit()
        ctime+=10
        self.cur.execute('select count(*) cnt from sgs where sgtype = 1 and value = 1')
        if self.cur.fetchall()[0][0] == 0 :
            self.cur.execute('select max(valuetime) maxtime from sgs where sgtype = 1 and value = 0')
            ls = self.cur.fetchall()
            t = ls[0][0]
            ctime = t if t != None else ctime
        return ctime

    def CheckCommand(self):
        ret = None
        ctime = time.time()
        self.cur.execute('update sgs set value = 0, valuetime = ? where sgtype in (5,6,7,8) and value = 1 and ?-valuetime  > 5',\
                         [ctime,ctime])
        self.con.commit()
        self.cur.execute('select * from sgs where sgtype in (5,6,7,8) and value > 0')
        l = self.cur.fetchall()
        if len(l) > 0 :
            ret = l[0]
        return ret





    def SetSgValue(self,sgid, sgvalue):
        try :
            self.cur.execute('select value from sgs where id_sg = ?',[sgid])
            rows=self.cur.fetchall()
            if len(rows)>0:
                pval = rows[0][0]
                if pval != sgvalue :
                    self.cur.execute('update sgs set value=?, valuetime=? where id_sg=?',[sgvalue,time.time(),sgid])
                    self.con.commit()
        except :
            se = sys.exc_info()
            logs.log.writelog('Ошибка при записи значения сигнал в БД sg='+str(sgid)+' value='+str(sgvalue)+' \n'+\
                              str(se[1]+'\n'+se[2].tb_frame.f_code))

    def GetSensors(self):
        self.cur.execute("select * from vsgs where sgtype in (1,5,6,7,8) and sgname <> 'n'")
        return MyrecordSet.MyRecordset(self.cur.fetchall(),self.cur.description)

    def GetTestValue(self,asgid):
        self.cur.execute("select * from sgvalues_test where sgid=?",[asgid])
        rows=self.cur.fetchall()
        res = int(rows[0][1]) if len(rows) > 0  else None
        return res



mdb = MuseumDB()


class Params:
    def __init__(self):
        self.paramlist = mdb.GetParams()
        logs.log.loglevel = self.loglevel()

    def ParamValue(self,paramnic):
        for x in self.paramlist._rows :
            ret = self.paramlist.FieldValue(x,'paramnic')
            if ret == paramnic :
                return self.paramlist.FieldValue(x,'paramvalue')
        return None

    def port(self):
        return self.ParamValue('port')

    def baudrate(self):
        return self.ParamValue('baudrate')

    def loglevel(self):
        return int(self.ParamValue('loglevel'))

    def playfilecmd(self):
        return self.ParamValue('startsound_cmd')

    def stopfilecmd(self):
        return self.ParamValue('stopsound_templay')


params = Params()



