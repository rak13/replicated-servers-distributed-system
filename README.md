1. Run coordinator.py 
	you may use:
	python coordinator.py  
	or, 
	python3 coordinator.py

	(You may even use your desired IDE)

2. You will find something like this:
	uri = PYRO:coordinator@192.168.137.1:3001

	use it to change the values (if required) of the following lines:

	coordinator_ip = "192.168.137.1"
	coordinator_port = "3001"

	in both server.py and client.py

3. run server.py 3 times (use 3 different terminals)
	
4. run client.py

5. perform client operations

6. stop a server and perform client operations and then restart server


NOTE:

Make sure that the 'server.py' and 'DBcontrol.py' are in the same folder
Never start more than 3 servers.
There are 4 accounts 401, 402, 403 and 404. Initially their balance will be 0.
Provide valid inputs, the client does not check for invalid inputs
If u restart the coordinator, it will be best to delete the log files and database files



