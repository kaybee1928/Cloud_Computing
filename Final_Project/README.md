# Cloud-Computing Final Project

## About



### Orchestrator:

1. Has APIs writedb, readdb, crash_slave, crash_master, list_workers.
2. writedb publishes request on to writeQ along with requestID and waits for response in responseQ that has required requestID.
3. readdb publishes request on to readQ along with requestID and waits for response in responseQ that has required requestID.
4. crash_slave stops a slave and return pid. Event of creating new slave is triggered only if there is one slave.
5. crash_slave stops the master and return pid. Event of electing new master is triggered.
6. returns list of PIDs of worker.
7. Zookeper watches over master and slave.
* i) in case of failure of slave a new slave container is brought up.
* ii) in case of failure of master a new master is elected.
8. Scale up and scale down happens according to read count.
* i) Scale up happens immediately
* ii) Scale down happens every two minutes
* iii) Read count is reset every two minutes


### Election:

1.Using signals like SIGTERM handling we elect slave to master.


### Slave/Master:

1. creates a slave node in zookeeper as soon as it is started.
2. if SIGTERM is received it becomes master.
3. if SIGQUIT is received it dies.
4. when it is slave it listens to readQ and syncQ.
* i) on receiving request from readQ, it will process the same and pushes response onto responseQ.
* ii) on receiving request from syncQ it will make changes to database.
5. when it is master it listens to writeQ.
* i) on receiving request from writeQ, it will process the same and pushes response onto responseQ.
6. On crash or death it will delete it's node from zookeper.

### DB-Manager

1. Ensures that database is replicated properly in slave when slave is started.


## How to run

### User

```bash
    cd users
    sudo docker-compose up --build
```

### Rides

```bash
    cd rides
    sudo docker-compose up --build
```

### Orchestrator

```bash
    cd Orchestrator
    sudo docker-compose up --build
```

