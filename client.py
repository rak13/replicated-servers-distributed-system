
import sys
import Pyro4

if sys.version_info<(3,0):
    input = raw_input

coordinator_ip = "192.168.0.5"
coordinator_port = "3001"

coordinator_uri = "PYRO:coordinator@"+coordinator_ip+":"+coordinator_port
coordinator = Pyro4.Proxy(coordinator_uri)

while True:
    print ("B for Balance")
    print ("D for Deposit")
    print ("W for withdrawal")
    command = input()

    if(command == 'B'):
        ac_num = input("Enter Account number (eg: 401, 402) ")
        print('Balance for A/C:', ac_num, " = ", coordinator.getBalance(ac_num))
    elif (command == 'W'):
        ac_num = input("Enter Account number (eg: 401, 402) ")
        val = input("Enter Wihdrawal amount (ed: 100) ")
        coordinator.withdraw(ac_num, int(val))
    else:
        ac_num = input("Enter Account number (eg: 401, 402) ")
        val = input("Enter Deposit amount (ed: 100) ")
        coordinator.deposit(ac_num, int(val))
