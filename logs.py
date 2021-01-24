import datetime
import os



class LogClass :
    def __init__(self,a_path,a_prefix = 'log'):
        self.path = a_path
        self.prefix = a_prefix
        self.loglevel = 0
        self.days = 2


    def getFileMask(self):
        return self.path+'/'+self.prefix

    def getFileName(self):
        return self.getFileMask()+str(datetime.date.today()).replace('-','')+'.log'



    def writelog(self,logstr, alevel=0):
        if self.loglevel >= alevel:
            filename = self.getFileName()
            if os.path.exists(filename) :
                mode = 'a'
            else :
                mode = 'w'
                self.deleteOldFiles()
            f=open(filename,mode)
            n=f.write(str(datetime.datetime.now())+' : '+logstr+'\n')
            f.close()

    def deleteOldFiles(self):
        olddate = datetime.date.today() - datetime.timedelta(self.days)
        oldfilename = self.prefix+str(olddate).replace('-','')+'.log'
        filelist = filter(lambda x: x.startswith(self.prefix) and x.endswith('.log') and (x< oldfilename) , os.listdir(self.path))
        for x in filelist:
            #print x
            os.remove(self.path+'/'+x)



log = LogClass('./logs','lm')
log.deleteOldFiles()
