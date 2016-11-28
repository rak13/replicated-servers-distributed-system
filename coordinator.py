from __future__ import print_function
from threading import Semaphore
from multiprocessing.dummy import Pool
from functools import partial

import Pyro4
import sys
import threading
import time
import socket

if sys.version_info<(3,0):
    input = raw_input


pool = Pool(processes=3)

accounts = ['401','402','403','404']

@Pyro4.expose
class Coordinator(object):

    def __init__(self):

        # Critical Region - avoid multiple calls to semaphore_on_accountss
        self.CR = Semaphore(1)

        # check if resync is in progress
        self.resyncing = False

        self.list_of_server_locks = {}

        self.list_of_servers = set()

        # Thread for heart beat
        t = threading.Thread(target=self.heart_beat,args=())
        t.start()

    def setServer(self, serv_uri):
        self.list_of_servers.add(serv_uri)
        self.list_of_server_locks[serv_uri] = set()
        self.semaphore_on_accounts = {account:Semaphore(1) for account in accounts}
        print ("Server has been registered : " + serv_uri)

    def releaseAccountWithCnt(self, state, server_uri, account_num):
        # use semaphore to avoid multiple calls to semaphore_on_accounts[account_num].release()
        self.CR.acquire()

        # remove account under this server
        print(server_uri, " Releasing account: ", account_num)
        self.list_of_server_locks[server_uri].remove(account_num)

        allDone = True
        for server_uri in self.list_of_server_locks:
            if account_num in self.list_of_server_locks[server_uri]:
                allDone = False
                break

        # release an accounts semaphore if no server holds it
        if allDone:
            print("Release account ", account_num)
            self.semaphore_on_accounts[account_num].release()

        self.CR.release()

    def getBalance(self, account_num):

        while self.resyncing:
            temp = 1

        final_balance = -1
        #lock the account
        print("Lock account ", account_num)
        self.semaphore_on_accounts[account_num].acquire()

        for serv_uri in self.list_of_servers:
            server = Pyro4.Proxy(serv_uri)
            cur_balance = server.getBalance(account_num)
            if final_balance == -1:
                final_balance = cur_balance
            # Inconsistant if servers have different final_balance
            else:
                if(final_balance != cur_balance):
                    print ("Inconsistant servers")

        self.semaphore_on_accounts[account_num].release()
        print("Release account ", account_num)
        return final_balance

    def deposit(self, account_num, amount):
        while self.resyncing:
            temp = 1

        print("Lock account ",account_num)
        self.semaphore_on_accounts[account_num].acquire()

        print ("Depositing... ")
        for serv_uri in self.list_of_servers:
            self.list_of_server_locks[serv_uri].add(account_num)

        # Deposit on each server is simulated asynchronously
        for serv_uri in self.list_of_servers:
            server = Pyro4.Proxy(serv_uri)
            dep_callback = partial(self.releaseAccountWithCnt,server_uri=serv_uri,account_num=account_num) #use partial to pass parameters to the callback
            pool.apply_async(
                server.deposit,
                args=[account_num,amount],
                callback=dep_callback
            )


    def withdraw(self, account_num, amount):
        while self.resyncing:
            temp = 1

        print("Lock account ", account_num)
        self.semaphore_on_accounts[account_num].acquire()

        print("Withdrawing...")

        for serv_uri in self.list_of_servers:
            self.list_of_server_locks[serv_uri].add(account_num)

        # Withdraw on each server is simulated asynchronously
        for serv_uri in self.list_of_servers:
            server = Pyro4.Proxy(serv_uri)
            wit_callback = partial(self.releaseAccountWithCnt,server_uri=serv_uri,account_num=account_num)
            pool.apply_async(
                server.withdraw,
                args=[account_num,amount],
                callback=wit_callback
            )

    def resync(self):
        self.resyncing = True

    def doneresync(self):
        self.resyncing = False

    def getUriOfOtherServers(self, server_uri):
        # returns URI of registered servers except server_uri
        list_of_uris = []
        for serv_uri in self.list_of_servers:
            if serv_uri != server_uri:
                list_of_uris.append(serv_uri)
        return list_of_uris


    def heart_beat(self):
        #checks availabity of each registered server every second
        while True:
            for serv_uri in list(self.list_of_servers):
                try:
                    server = Pyro4.Proxy(serv_uri)
                    server.isAlive()
                    print ("Server ", serv_uri, ": is still Alive")
                except:
                    print(serv_uri,": is unreachable, releasing semaphores")
                    for account in list(self.list_of_server_locks[serv_uri]):
                        # release locked accounts by this server
                        self.releaseAccountWithCnt(None,serv_uri,account)
                    self.list_of_servers.remove(serv_uri)

            time.sleep(1)

def get_my_ip():
    SC = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SC.connect(("8.8.8.8", 80))
    return SC.getsockname()[0]

def main():
    CO = Coordinator()
    ip = get_my_ip()
    Pyro4.Daemon.serveSimple(
        host=ip,
        objects={
            CO: "coordinator"
        },
        port=3001,
        ns = False)

if __name__=="__main__":
    main()