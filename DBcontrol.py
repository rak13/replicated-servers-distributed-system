import json
import Pyro4

@Pyro4.expose
class DataBase(object):
    def __init__(self,filename):
        self.dbfile = 'database'+str(filename)
        init_DB = {"401":0,"402":0,"403":0,"404":0}
        file_p = open(self.dbfile,'w')
        json.dump(init_DB,file_p)
        file_p.close()

    def setBalance(self, ac_number, ac_balance):
        file_p = open(self.dbfile, 'r')
        cur_db = json.load(file_p)
        cur_db[ac_number] = ac_balance
        file_p = open(self.dbfile, "w")
        json.dump(cur_db, file_p)

    def getBalance(self, ac_number):
        ac_number = str(ac_number)
        file_p = open(self.dbfile,'r')
        cur_db = json.load(file_p)
        file_p.close()
        return cur_db[ac_number]