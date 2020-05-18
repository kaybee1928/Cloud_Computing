import pika
import re
import json
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, abort, Response
import docker
import threading
from kazoo.client import KazooClient
from kazoo.client import KazooState
import logging
import os
import signal
import time
#import subprocess

app = Flask(__name__)

############################# RABBITMQ QUEUE DECLERATION #############################

connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq', heartbeat=0))
channel = connection.channel()

channel.queue_declare(queue='writeQ')
channel.queue_declare(queue='readQ')
######################################################################################


################################ ZOOKEPER VARIABLES ##################################

logging.basicConfig()
zk = KazooClient(hosts='zoo:2181')
zk.start()

zk.ensure_path("/slave")
zk.ensure_path("/master")
######################################################################################



############# DOCKER CLIENT AND OTHER ARGUMENTS FOR CONTAINERS STARTING ##############

net_mode = "orchestrator_default"
path = "/root/Documents/Cloud/Project/Project/cc/Orchestrator/"
vol = {path:{"bind":"/mnt/code", "mode":"rw"}}
links = {"rmq":"rmq", "zoo":"zoo"}
client = docker.DockerClient(base_url='tcp://172.31.82.57:2375')
######################################################################################


sssss = 1

# Time between slave container starting and master election
firstElection = 3

# Booleans to perform locks and manipulate flow of program
current_master = None
masterPresent = False
globalLock = True
globalreadLock = True

# Dictionaries to store the responses from the worker
responseDict = {}
responseWDict = {}


def deleteUnwantedWorker():
    """
        On execution of orchestrator.py this function executes.
        Checks whether the nodes in master and slave path are
        still running.
        Nodes that are not running are removed without triggering
        watcher function.
    """
    m = zk.get_children("/master")
    s = zk.get_children("/slave")
    for i in s:
        cid = zk.get("/slave/"+i)[0].decode()
        sl = client.containers.get(cid)
        if(sl.attrs['State']['Status'] == 'running'):
            pass
        else:
            zk.delete("/slave/"+i)

    for i in m:
        cid = zk.get("/master/"+i)[0].decode()
        sl = client.containers.get(cid)
        if(sl.attrs['State']['Status'] == 'running'):
            pass
        else:
            zk.delete("/master/"+i)

    time.sleep(1.5)



def getResponseW():
    """
        Reads the response for write request from responsewQ.
        Pushes the response onto responseWDict with requestID
        as the key.
    """
    global responseWDict
    connection2 = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq', heartbeat=0))
    channel2 = connection2.channel()

    channel2.queue_declare(queue = "responsewQ")
    while(True):
        res = channel2.basic_get(queue="responsewQ")

        # dequeque from `responsewQ` until response is got 
        while(res[2]==None):
            res = channel2.basic_get(queue="responsewQ")

        data = json.loads(res[2])
        reqID = int(list(data.keys())[0])
        
        responseWDict[reqID] = data[str(reqID)]

def getResponse():
    """
        Reads the response for read request from responseQ.
        Pushes the response onto responseDict with requestID
        as the key.
    """
    global responseDict
    connection3 = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq', heartbeat=0))
    channel3 = connection3.channel()
    channel3.queue_declare(queue = "responseQ")
    while(True):
        res = channel3.basic_get(queue="responseQ")

        # dequeque from `responseQ` until response is got 
        while(res[2]==None):
            res = channel3.basic_get(queue="responseQ")

        data = json.loads(res[2])
        print(data)
        reqID = int(list(data.keys())[0])
        responseDict[reqID] = data[str(reqID)]





def downScale():
    """
        Performs down scaling if required condition is met
        Takes a read lock on all slaves and performs down scale.
        When lock is acquired master election and scale up cannot
        be performed.
    """
    global globalreadLock
    while(True):
        time.sleep(0.01)
        ttt = open("timer.txt", "r")
        tt = float(ttt.readline())
        while(time.time()-tt<120):
            pass
        slaves_pid = getOnlyInt(zk.get_children("/slave"))
        while(globalreadLock == False):
            pass
        globalreadLock = False
        fff = open("counter.txt", "r")
        count = int(fff.readline())
        cc = len(slaves_pid) - (int((count-1) / 20) + 1)
        while(cc>0):
            requests.post(url = 'http://0.0.0.0:8080/api/v1/crash/slave')
            cc = cc - 1
        fff.close()
        fff = open("counter.txt", "w")
        fff.write(str(0))
        fff.close()
        globalreadLock = True
        ttt.close()
        ttt = open("timer.txt", "w")
        ttt.write(str(time.time()))
        ttt.close()



def ReadIsToSlave():
    """
        Performs up scaling if required condition is met
        Takes a read lock on all slaves and performs up scale.
        When lock is acquired master election and scale down cannot
        be performed.
    """
    global globalreadLock
    while(globalreadLock == False):
        pass
    globalreadLock = False
    fff = open("counter.txt", "r")
    count = int(fff.readline())
    count = count + 1
    fff.close()
    fff = open("counter.txt", "w")
    fff.write(str(count))
    slaves_pid = getOnlyInt(zk.get_children("/slave"))
    cc = int((count-1) / 20) + 1 - len(slaves_pid)
    while(cc>0):
        slavePatrols(1)
        time.sleep(3)
        cc = cc - 1
    globalreadLock = True



def getOnlyInt(arr):
    """
        Accepets an list or iterable as arr
        return list of elements that can be converted
        into integer from arr as integer
    """
    a = []
    for i in arr:
        try:
            a.append(int(i))
        except:
            pass
    return a



def firstElectionTimer():
    """
        Timer that starts everytime a slave is created
        Used to wait for slave to get ready for master election
    """
    global firstElection
    time.sleep(3)
    firstElection = 0


def slavePatrols(ev):
    """
        Watches over all slave nodes.
        In case of failure of a slave this function is triggered.
        If there is a master and data-base is modified, master is
        commited on slave image.
        New slave is started and db_manager makes sure that master 
        db is replicated properly in the slave.
    """
    global masterPresent
    global current_master
    global firstElection
    firstElection = 3
    if(masterPresent==True):
        try:
            current_master.commit('slave:latest')
            masterPresent = False
        except Exception as e:
            print(e)
        time.sleep(0.5)
    slave = client.containers.run("slave:latest", network_mode="orchestrator_default", 
            links=links, command="python3 slave.py", detach = True)
    time.sleep(2)
    slave.exec_run(["python3", "/usr/src/app/db_manager.py"])
    firstElection = 3
    timer = threading.Thread(target=firstElectionTimer, args=())
    timer.start()
    children = getOnlyInt(zk.get_children("/slave", watch=slavePatrols))
    return slave.id
    
    
    

def masterElection(ev):
    """
        Watches over master node.
        In case of failure of a master this function is triggered.
        If no master is present a new master is elected from slaves.
        Slave with least PID is elected as master.
        Read lock is acquired here which stops upsacling and down-scaling
        to happen until new master is created.
    """
    global globalreadLock
    global masterPresent
    global current_master
    masterPresent = True
    slaves = dict()
    masters = getOnlyInt(zk.get_children("/master"))
    if(len(masters) == 0):
        while(globalreadLock == False):
            pass
        globalreadLock = False
        global firstElection
        time.sleep(firstElection)
        slaves_pid = getOnlyInt(zk.get_children("/slave", watch=slavePatrols))
        for slave in slaves_pid:
            print(zk.get("/slave/"+str(slave)))
            slaves[slave] = zk.get("/slave/"+str(slave))[0].decode()
        slaves_pid = sorted(slaves_pid)
        time.sleep(firstElection)
        cont_id = zk.get("/slave/"+str(slaves_pid[0]))[0].decode()
        
        slave = client.containers.get(cont_id)
        time.sleep(firstElection)
        sss=slave.exec_run(["kill","1"])
        current_master = slave
        time.sleep(2)
        globalreadLock = True
        return slave.id
    return 0
    




@app.route('/api/v1/db/write', methods=['POST'])
def db_write():
    '''
        write request is taken and
        passed to writeQ
    '''

    fff = open("WreqID.txt", 'r')
    reqID = int(fff.readline()) + 1
    fff.close()
    fff = open("WreqID.txt", 'w')
    fff.write(str(reqID))
    fff.close()
    data = request.get_json()

    body = {}
    body[reqID] = data

    # publish the data onto the `writeQ` queue
    channel.basic_publish(exchange='', routing_key='writeQ', body=json.dumps(body))
    global masterPresent
    masterPresent = True

    # getting response from the `responseQ` queue
    

    # dequeque from `responseQ` until response is got 
    print(reqID)
    global responseWDict
    while (reqID not in list(responseWDict.keys())):
        time.sleep(0.01)

    res = responseWDict[reqID]
    responseWDict.pop(reqID)


    return jsonify(json.loads(res["result"])), res["status"]



@app.route('/api/v1/db/read', methods=['POST'])
def db_read():
    '''
        read request is taken and
        passed to readQ
        counter on read is increased and upscaling is done if required
    '''

    fff = open("RreqID.txt", 'r')
    reqID = int(fff.readline()) + 1
    fff.close()
    fff = open("RreqID.txt", 'w')
    fff.write(str(reqID))
    fff.close()
    # data from `post` request
    data = request.get_json()

    body = {}
    body[reqID] = data

    # publish the data onto the `readQ` queue
    channel.basic_publish(exchange='', routing_key='readQ', body=json.dumps(body))

    
    counter = threading.Thread(target=ReadIsToSlave, args=())
    counter.start()
    

    # getting response from the `responseQ` queue

    # dequeque from `responseQ` until response is got 
    print(reqID)
    global responseDict
    while (reqID not in list(responseDict.keys())):
        fff = open("www.txt", 'w')
        fff.write(json.dumps(responseDict))
        fff.close()

    res = responseDict[reqID]
    responseDict.pop(reqID)


    return jsonify(json.loads(res["result"])), res["status"]




@app.route("/api/v1/worker/list", methods=['GET'])
def list_workers():
    """
        Lists all PIDs of workers that are running.
        PIDs of both master and slaves are sorted
        and returned back in this API.
    """
    slaves = getOnlyInt(zk.get_children("/slave"))
    master = getOnlyInt(zk.get_children("/master"))
    res = sorted(slaves+master)
    if(len(res)==0):
        return jsonify([]),204
    return jsonify(res),200




@app.route("/api/v1/crash/slave", methods=['POST'])
def crash_slave():
    """
        Crashes a slave and return it's PID when called.
        slavePatrols is triggered only when one slave is 
        present before crashing.
        Lock is aquired which makes crash_master wait until 
        crash_slave done it's job
    """
    global globalLock
    while (globalLock == False):
        pass
    globalLock = False
    try:
        children = getOnlyInt(zk.get_children("/slave"))
        if(len(children)<=1):
            children = getOnlyInt(zk.get_children("/slave", watch=slavePatrols))
        time.sleep(0.3)
        children = sorted(children, reverse=True)
        pid = children[0]
        cont_id = zk.get("/slave/"+str(pid))[0].decode()
        slave = client.containers.get(cont_id)
        slave.exec_run(["kill","-QUIT","1"])
        while(slave.attrs['State']['Status'] == 'running'):
            slave = client.containers.get(cont_id)
        globalLock = True
    except:
        globalLock = True
        time.sleep(3)
        rr =  requests.post(url = 'http://0.0.0.0:8080/api/v1/crash/slave')
        return rr.json(),rr.status_code
    children = getOnlyInt(zk.get_children("/slave", watch=slavePatrols))
    return jsonify({'pid':int(pid)}),200


@app.route("/api/v1/crash/master", methods=['POST'])
def crash_master():
    """
        Crashes a master and return it's PID when called.
        masterElection is triggered.
        Lock is aquired which makes crash_slave wait until 
        crash_master done it's job.
    """
    global globalLock
    while (globalLock == False):
        pass
    globalLock = False
    try:
        children = getOnlyInt(zk.get_children("/master", watch=masterElection))
        children = sorted(children)
        pid = children[0]
        cont_id = zk.get("/master/"+str(pid))[0].decode()
        master = client.containers.get(cont_id)
        master.exec_run(["kill","1"])
        while(master.attrs['State']['Status'] == 'running'):
            master = client.containers.get(cont_id)
        globalLock = True
    except:
        globalLock = True
        time.sleep(3)
        rr = requests.post(url = 'http://0.0.0.0:8080/api/v1/crash/master')
        return rr.json(),rr.status_code

    return jsonify({'pid':int(pid)}),200




def init_sm():
    """
        Initializes master and slave.
        Deletes Unwanted nodes from master and slave path.
        created slave and elects a master if required.
        Starts down scaling and response receiving threads.
    """
    deleteUnwantedWorker()
    zk.ensure_path("/slave")
    
    zk.ensure_path("/master")
    slavePatrols(1)
    time.sleep(3)
    masterElection(1)
    dscale = threading.Thread(target=downScale, args=())
    dscale.start()
    resp = threading.Thread(target=getResponse, args=())
    resp.start()
    respW = threading.Thread(target=getResponseW, args=())
    respW.start()
    return True


# Initalize master and slave   
init_sm()
