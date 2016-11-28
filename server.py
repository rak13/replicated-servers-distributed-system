from __future__ import print_function
import Pyro4
import sys
import json
import time
import os.path
import os
import socket
from DBcontrol import DataBase

if sys.version_info<(3,0):
    input = raw_input

coordinator_ip = "192.168.0.5"
coordinator_port = "3001"

@Pyro4.expose
class Server(object):
    def __init__(self, id,port):
        self.id = id
        self.DB = DataBase(id)
        self.this_server_uri = "PYRO:server"+str(id)+"@"+get_ip_address()+":"+str(port)

        # number of operations
        self.count_of_operations = 0

        self.log_file_name = "log" + str(id)

        coordinator_uri = "PYRO:coordinator@"+coordinator_ip+":"+coordinator_port
        coordinator = Pyro4.Proxy(coordinator_uri)

        # If logfile exist then this isn't the servers first time
        if os.path.isfile(self.log_file_name):
            self.resync(coordinator)

        #register current server to coordinator
        coordinator.setServer(self.this_server_uri)

    def isAlive(self):
        return True

    def getBalance(self, account_no):
        balance = self.DB.getBalance(account_no)
        print(" Server#" + str(self.id) + " Balance : \t\t\t" + str(account_no) + "\t\t\t" + str(balance) + "\n")
        return balance

    def deposit(self, account_no, amount):
        self.count_of_operations += 1
        cur_balance = self.DB.getBalance(ac_number=account_no)
        cur_balance = cur_balance+amount
        self.DB.setBalance(account_no, cur_balance)
        with open(self.log_file_name,'a') as file_p:
            file_p.write(str(self.count_of_operations)+" "+str(account_no)+" "+str(cur_balance)+"\n")

        print (str(self.count_of_operations)+" Server#"+str(self.id) +" deposits : \t\t\t"+str(account_no)+"\t\t\t"+str(amount)+"\n")

        # simulate delay
        time.sleep(5)

        return cur_balance

    def withdraw(self, account_no, amount):
        self.count_of_operations += 1
        cur_balance = self.DB.getBalance(ac_number=account_no)

        if ((cur_balance - amount) < 0):
            print("Server#" + str(self.id) + " failed to withdraw , not enough balance")
            return -1
        else :
            cur_balance = cur_balance - amount
            self.DB.setBalance(account_no, cur_balance)

        with open(self.log_file_name,'a') as file_p:
            file_p.write(str(self.count_of_operations)+" "+str(account_no)+" "+str(cur_balance)+"\n")

        print (str(self.count_of_operations)+" Server#"+str(self.id) +" withdraws : "+"\t\t\t"+str(account_no)+"\t\t\t-"+str(amount)+"\n")

        # simulate delay
        time.sleep(5)
        return cur_balance


    def getLastLine(self, filename):
        # return last line of a file
        last_Line = ''
        with open(filename, 'r') as file_p:
            for line in file_p:
                last_Line = line
        return last_Line

    def resync(self,coordinator):

        # similar to sending "ALIVE" message
        coordinator.resync()

        otherServers = coordinator.getUriOfOtherServers(self.this_server_uri)

        last_Line = self.getLastLine(self.log_file_name)
        # print("last line = ", last_Line)
        if len(last_Line) == 0:
            # nothing to sync
            last_Line = '-1 0 0'
        for server_name in otherServers:
            server = Pyro4.Proxy(server_name)

            operationsNotSeen = server.updateLog(last_Line)
            print(operationsNotSeen)
            for acc in operationsNotSeen:
                self.DB.setBalance(acc,operationsNotSeen[acc])
        #Flush logfile
        open(self.log_file_name, 'w').close()

        # similar to sending "RESYNCH-DONE" message
        coordinator.doneresync()

    def updateLog(self, last_Line):
        # update the log file
        print(last_Line)
        lastOp = int(last_Line.strip().split()[0])

        # holds updates info of accounts
        updatedAcnts = {}

        with open(self.log_file_name,'r') as file_p:

            for line in file_p:
                print(line)
                l = line.strip().split()
                if int(l[0]) > lastOp:
                    #if this operation number is greater, update the log
                    updatedAcnts[l[1]] = int(l[2])

        #updated server and flush log file
        open(self.log_file_name, 'w').close()
        return updatedAcnts


def get_ip_address():
    SC = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SC.connect(("8.8.8.8", 80))
    return SC.getsockname()[0]

def main():

    inp = input("Enter server id (eg: 1): ").strip()
    id = int(inp)
    inp = input("Enter server port# (eg, 4001) ").strip()
    port = int(inp)

    SERVER = Server(id, port)

    ip = get_ip_address()

    Pyro4.Daemon.serveSimple(
        host=ip,
        objects={
            SERVER: "server"+str(id)
        },
        port=port,
        ns=False)

if __name__=="__main__":
    main()