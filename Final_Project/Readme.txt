# Cloud-Computing Final Project

### Orchestrator:
1. Has APIs writedb, readdb, crash_slave, crash_master, list_workers.
2. writedb publishes request on to writeQ along with requestID and waits for response in responseQ that has required requestID.
3. readdb publishes request on to readQ along with requestID and waits for response in responseQ that has required requestID.
4. crash_slave stops a slave and return pid. Event of creating new slave is triggered only if there is one slave.
5. crash_slave stops the master and return pid. Event of electing new master is triggered.
6. returns list of PIDs of worker.
7. Zookeper watches over master and slave.
	i) in case of failure of slave a new slave container is brought up.
	ii) in case of failure of master a new master is elected.


### Election:
1.Using signals like SIGTERM handling we elect slave to master.


### Slave/Master:
1. creates a slave node in zookeeper as soon as it is started.
2. if SIGTERM is received it becomes master.
3. if SIGQUIT is received it dies.
4. when it is slave it listens to readQ and syncQ.
	i) on receiving request from readQ, it will process the same and pushes response onto responseQ.
	ii) on receiving request from syncQ it will make changes to database.
5. when it is master it listens to writeQ.
	i) on receiving request from writeQ, it will process the same and pushes response onto responseQ.
6. On crash or death it will delete it's node from zookeper.



### DB-Manager:

1. Ensures that database is replicated properly in slave when slave is started.


## How to run:
1. create three EC2 instances on AWS.
2. create tw target groups for the rides and users microservices
3. deploy the two microservices over a application load balancer
4. install docker and docker-compose on the three instances and configure nginx as required
5. change the IP addresses in all the codes are required.
6. Build and deploy the docker images as directed
7. User:
    $ cd users
    $ sudo docker-compose up --build
8. Rides:
    $ cd rides
    $ sudo docker-compose up --build
9. Orchestrator:
    $ cd Orchestrator
    $ sudo docker-compose up --build

