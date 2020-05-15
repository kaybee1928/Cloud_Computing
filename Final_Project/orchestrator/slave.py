import re
import pika
import json
import threading 
import time
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, abort, Response
import docker
from kazoo.client import KazooClient
from kazoo.client import KazooState
import logging
import os
import signal
import time
import atexit
import sys 


############# DOCKER CLIENT AND OTHER ARGUMENTS FOR CONTAINERS STARTING ##############

net_mode = "orchestrator_default"
path = "/root/Documents/Cloud/Project/Project/cc/Orchestrator/"
vol = {path:{"bind":"/mnt/code", "mode":"rw"}}
links = {"rmq":"rmq", "zoo":"zoo"}
client = docker.DockerClient(base_url='tcp://172.31.82.57:2375')
######################################################################################

# Get the current working container
this = client.containers.get(os.uname()[1])


################################ ZOOKEPER VARIABLES ##################################

logging.basicConfig()
zk = KazooClient(hosts='zoo:2181')
zk.start()
notDead = True
zk.ensure_path("/slave")
zk.ensure_path("/master")
######################################################################################



def db_write(request):
    """
        Takes in request and does write operation on DB
        return data, status_code
    """
    # Extract the json data
    data = request

    if data['api'] == 'add_user':
        username = data['username']
        password = data['password']

        # Add the user to the database
        users_data = pd.read_csv('users.csv')
        print(users_data)
        users_data = users_data.append({'username': username, 
            'password': password}, ignore_index=True)
        users_data.to_csv('users.csv', index=False)

        return json.dumps({}), 201

    if data['api'] == 'delete_user':
        username = data['username']

        # Remove user data from rides database
        rides_data = pd.read_csv('rides.csv')
        rides_data = rides_data[rides_data.created_by != username]
        riders_data = list(rides_data.riders)
        for index in range(len(riders_data)):
            riders = riders_data[index]
            riders = riders.split(',')
            if username in riders:
                riders.remove(username)
            riders_data[index] = ','.join(riders)
        rides_data.riders = riders_data
        rides_data.to_csv('rides.csv', index=False)

        # Remove user form the user database
        users_data = pd.read_csv('users.csv')
        users_data = users_data[users_data.username != username]
        users_data.to_csv('users.csv', index=False)

        return json.dumps({}), 200

    if data['api'] == 'users_db_clear':
        # Clear the rides database
        db_write({'api':'rides_db_clear'})

        # Clear the users database
        users = pd.DataFrame({'username':[], 'password':[]})
        users.to_csv('users.csv', index=False)

        return json.dumps({}), 200

    if data['api'] == 'reset_users_api_request_count':
        # Reset the requests count
        rides_count = open('users_api_requests_count.txt','w')
        rides_count.write(str(0))
        rides_count.close()

        return json.dumps({}), 200

    if data['api'] == 'increment_users_api_request_count':
        # Read the latest requests_count
        requests_count = open('users_api_requests_count.txt','r')
        last_requests_count = requests_count.read()
        requests_count.close()

        # Update the latest requests_count
        current_requests_count = int(last_requests_count) + 1
        requests_count = open('users_api_requests_count.txt','w')
        requests_count.write(str(current_requests_count))
        requests_count.close()

        return json.dumps({}), 200

    if data['api'] == 'new_ride':
        created_by = data['created_by']
        timestamp = data['timestamp']
        source = data['source']
        destination = data['destination']

        # Read the latest rideId
        file = open('latest_rideId.txt','r')
        last_rideId = file.read()
        file.close()

        # Update the latest rideId to generate new rideId
        current_rideId = int(last_rideId) + 1
        file = open('latest_rideId.txt','w')
        file.write(str(current_rideId))
        file.close()

        # Add the ride detials to the database
        rides_data = pd.read_csv('rides.csv')
        rides_data = rides_data.append({'rideId': current_rideId, 
            'created_by': created_by, 'riders': created_by, 
            'timestamp': timestamp, 'source': source, 
            'destination': destination}, ignore_index=True)
        rides_data.to_csv('rides.csv', index=False)

        return json.dumps({}), 201

    if data['api'] == 'join_ride':
        rideId = data['rideId']
        username = data['username']

        # Add user to the ride
        rides_data = pd.read_csv('rides.csv')
        for index in range(len(rides_data)):
            if int((rides_data.rideId)[index]) is int(rideId):
                riders_list = rides_data.loc[index, 'riders'].split(',')
                if username not in riders_list:
                    riders_list.append(username)
                rides_data.loc[index, 'riders'] = ','.join(riders_list)
                rides_data.to_csv('rides.csv', index=False)
                return json.dumps({}), 200

    if data['api'] == 'delete_ride':
        rideId = data['rideId']

        # Delete the ride from the database
        rides_data = pd.read_csv('rides.csv')
        initial_number_of_rides = len(rides_data)
        rides_data = rides_data[rides_data.rideId != int(rideId)]
        final_number_of_rides = len(rides_data)
        rides_data.to_csv('rides.csv', index=False)

        return json.dumps({}), 200

    if data['api'] == 'rides_db_clear':
        # Clear the rides database
        rides = pd.DataFrame({'rideId': [], 'created_by': [], 
            'riders': [], 'timestamp': [], 'source':[], 
            'destination':[]})
        rides.to_csv('rides.csv', index=False)
        file = open('latest_rideId.txt','w')
        file.write('0')
        file.close()

        return json.dumps({}), 200

    if data['api'] == 'reset_rides_api_request_count':
        # Reset the requests count
        requests_count = open('rides_api_requests_count.txt','w')
        requests_count.write(str(0))
        requests_count.close()

        return json.dumps({}), 200

    if data['api'] == 'increment_rides_api_request_count':
        # Read the latest requests_count
        requests_count = open('rides_api_requests_count.txt','r')
        last_requests_count = requests_count.read()
        requests_count.close()

        # Update the latest requests_count
        current_requests_count = int(last_requests_count) + 1
        requests_count = open('rides_api_requests_count.txt','w')
        requests_count.write(str(current_requests_count))
        requests_count.close()

        return json.dumps({}), 200



def db_read(request):
    """
        Takes in request and does read operation on DB
        return data, status_code
    """
    # Extract the json data
    data = request

    if data['api'] == 'add_user':
        return_data = dict()

        # Extract users from the users database
        response = json.loads(db_read({'api':'list_users'})[0])
        db_write({'api':'increment_users_api_request_count'})

        if response:
            existing_users = list(map(str, response))
            # Check if user exists in the database
            if data['username'] in list(existing_users):
                return_data['user_exists'] = True
            else:
                return_data['user_exists'] = False

        else:
            return_data['user_exists'] = False

        return json.dumps(return_data), 200

    if data['api'] == 'delete_user':
        return_data = dict()

        # Extract users from the users database
        response = json.loads(db_read({'api':'list_users'})[0])
        db_write({'api':'increment_users_api_request_count'})
        if response:
            existing_users = list(map(str, response))
            # Check if user exists in the database
            if data['username'] in list(existing_users):
                return_data['user_exists'] = True
            else:
                return_data['user_exists'] = False

        else:
            return_data['user_exists'] = False

        return json.dumps(return_data), 200

    if data['api'] == 'list_users':
        # Extract users from the users database
        existing_users = pd.read_csv('users.csv')['username']
        existing_users = list(map(str, existing_users))

        return json.dumps(existing_users), 200

    if data['api'] == 'get_users_api_request_count':
        # Read the latest requests_count
        requests_count = open('users_api_requests_count.txt','r')
        last_requests_count = requests_count.read()
        requests_count.close()

        return json.dumps([int(last_requests_count)]), 200

    if data['api'] == 'new_ride':
        return_data = dict()

        # Extract the AreaNameEnum from database
        area_name_enum = pd.read_csv('AreaNameEnum.csv')['Area No']

        # Check if source exists in the database
        if data['source'] in list(area_name_enum):
            return_data['source_exists'] = True
        else:
            return_data['source_exists'] = False

        # Check if the destination exists in the database
        if data['destination'] in list(area_name_enum):
            return_data['destination_exists'] = True
        else:
            return_data['destination_exists'] = False

        # Extract users from the users database
        response = json.loads(db_read({'api':'list_users'})[0])
        db_write({'api':'increment_users_api_request_count'})
        if response:
            existing_users = list(map(str, response))
            # Check if user exists in the database
            if data['username'] in list(existing_users):
                return_data['user_exists'] = True
            else:
                return_data['user_exists'] = False

        else:
            return_data['user_exists'] = False

        return json.dumps(return_data), 200

    if data['api'] == 'list_rides':
        # Extract the source and the destination
        source = data['source']
        destination = data['destination']

        # Validate the source and destination
        area_name_enum = pd.read_csv('AreaNameEnum.csv')['Area No']
        if source not in area_name_enum or destination not in area_name_enum:
            return json.dumps({'error':'source or destination not in database'}), 400

        # Get the list of all the rides from database from source to destination
        rides_data = pd.read_csv('rides.csv')
        rides_data = rides_data[rides_data.source == source]
        rides_data = rides_data[rides_data.destination == destination]

        # Extract the rides data from the dataframe
        rides_Id = list(rides_data.rideId)
        rides_Id = list(map(int, rides_Id))
        rides_created_by = list(rides_data.created_by)
        rides_created_by = list(map(str, rides_created_by))
        rides_timestamp = list(rides_data.timestamp)
        rides_timestamp = list(map(str, rides_timestamp))
        rides_data_returned = []

        # Get current time
        date_time = datetime.now()

        # Create the list of ride details to be returned
        for index in range(len(rides_data)):
            ride_date_time = datetime.strptime(rides_timestamp[index], '%d-%m-%Y:%S-%M-%H')

            # Add ride data to list if the ride is scheduled in the future
            if (ride_date_time-date_time).total_seconds() > 0:
                temp_dict = {'rideId': rides_Id[index], 
                    'username': rides_created_by[index],
                    'timestamp': rides_timestamp[index]}
                rides_data_returned.append(temp_dict)

        return json.dumps(rides_data_returned), 200

    if data['api'] == 'get_ride_details':
        # Access the rides database
        rides_data = pd.read_csv('rides.csv')
        rides_Id = list(rides_data.rideId)
        rides_Id = list(map(int, rides_Id))

        # If the rideId is not in the database
        if data['rideId'] not in rides_Id:
            return json.dumps({}), 200

        # Get the ride with the given rideId
        rides_data = rides_data[rides_data.rideId == int(data['rideId'])]
        ride_details = dict()
        ride_details['rideId'] = str(list(rides_data.rideId)[0])
        ride_details['created_by'] = str(list(rides_data.created_by)[0])
        ride_details['users'] = ((list(rides_data.riders)[0]).split(','))
        ride_details['users'].remove(ride_details['created_by'])
        ride_details['timestamp'] = str(list(rides_data.timestamp)[0])
        ride_details['source'] = str(list(rides_data.source)[0])
        ride_details['destination'] = str(list(rides_data.destination)[0])

        return json.dumps(ride_details), 200

    if data['api'] == 'join_ride':
        return_data = dict()

        # Extract users from the users database
        response = json.loads(db_read({'api':'list_users'})[0])
        db_write({'api':'increment_users_api_request_count'})
        if response:
            existing_users = list(map(str, response))
            # Check if user exists in the database
            if data['username'] in list(existing_users):
                return_data['user_exists'] = True
            else:
                return_data['user_exists'] = False

        else:
            return_data['user_exists'] = False

        # Access the rides database
        rides_data = pd.read_csv('rides.csv')

        # Extract the rideIds from the database
        rides_Id = list(rides_data.rideId)
        rides_Id = list(map(int, rides_Id))

        # If the rideId is not in the database
        if data['rideId'] in list(rides_Id):
            return_data['rideId_exists'] = True
        else:
            return_data['rideId_exists'] = False

        # Check if the ride is still valid
        if return_data['rideId_exists']:
            rides_data = rides_data[rides_data.rideId == int(data['rideId'])]
            current_time = datetime.now()
            ride_time = datetime.strptime(list(rides_data.timestamp)[0], '%d-%m-%Y:%S-%M-%H')
            if (ride_time-current_time).total_seconds() > 0:
                return_data['ride_valid'] = True
            else:
                return_data['ride_valid'] = False
        else:
            return_data['ride_valid'] = False

        # Check if the rider already exists
        if return_data['ride_valid']:
            rides_data = rides_data[rides_data.rideId == int(data['rideId'])]
            riders_list = list(list(rides_data.riders)[0].split(','))
            if data['username'] not in list(riders_list):
                return_data['can_add_rider'] = True
            else:
                return_data['can_add_rider'] = False

        return json.dumps(return_data), 200

    if data['api'] == 'delete_ride':
        return_data = dict()

        # Extract rideIds from the users database
        rides_Id = pd.read_csv('rides.csv')['rideId']
        rides_Id = list(map(int, rides_Id))

        # If the rideId is not in the database
        if data['rideId'] in list(rides_Id):
            return_data['rideId_exists'] = True
        else:
            return_data['rideId_exists'] = False

        return json.dumps(return_data), 200

    if data['api'] == 'count_rides':
        # Get the number of rides in the database
        rides_count = len(list(pd.read_csv('rides.csv')['rideId']))

        return json.dumps([rides_count]), 200

    if data['api'] == 'get_rides_api_request_count':
        # Read the latest requests_count
        requests_count = open('rides_api_requests_count.txt','r')
        last_requests_count = requests_count.read()
        requests_count.close()

        return json.dumps([int(last_requests_count)]), 200




class masterSlave(object):
    """
        type : specifies whether the object is master or slave
        thread : runs slave or master according to the type

        slave_target reads from readQ and syncQ and does
        the required operation on DB and pushes response onto 
        responseQ.

        master_target reads from writeQ and send the request to
        db_wrtie and pushes the same onto syncQ also pushes 
        response on to responsewQ.
    """
    def __init__(self):
        self.type = "slave"
        self.thread = threading.Thread(target=self.slave_target, args=())
        

    def slave_target(self):
        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq'))
        channel = connection.channel()

        channel.queue_declare(queue='readQ')
        channel.queue_declare(queue = "responseQ")
        
        channel.queue_declare(queue = "syncQ")
        channel.exchange_declare(exchange='logs', exchange_type='fanout')
        
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='logs', queue=queue_name)

        while(self.type=="slave"):
            body = channel.basic_get(queue="readQ")
            if(body[0]!=None):
                req = json.loads(body[2].decode('utf-8'))
                reqID = list(req.keys())[0]
                data = req[reqID]
                res = db_read(data)

                responses = {reqID : {"result":res[0], "status":res[1]}}
                responses = json.dumps(responses)

                channel.basic_publish(exchange='', routing_key='responseQ', body=responses)

            sync_counter = 5

            body = channel.basic_get(queue=queue_name)
            while(body[0]==None and sync_counter > 0):
                body = channel.basic_get(queue=queue_name)
                sync_counter = sync_counter - 1
            
            if(body[0]!=None):
                res = db_write(json.loads(str(body[2].decode('utf-8'))))
                responses = {"result":res[0], "status":res[1]}
                responses = json.dumps(responses)
        channel.close()
        connection.close()


    def master_target(self):
        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq'))
        channel = connection.channel()
        channel.exchange_declare(exchange='logs', exchange_type='fanout')
        channel.queue_declare(queue='writeQ')
        channel.queue_declare(queue='readQ')
        channel.queue_declare(queue = "responsewQ")

        while(self.type=="master"):
            body = channel.basic_get(queue="writeQ")
            
            if(body[0]!=None):
                req = json.loads(body[2].decode('utf-8'))
                reqID = list(req.keys())[0]
                data = req[reqID]
                res = db_write(data)
                responses = {reqID : {"result":res[0], "status":res[1]}}
                
                responses = json.dumps(responses)
                channel.basic_publish(exchange='', routing_key='responsewQ', body=responses)
                channel.basic_publish(exchange='logs', routing_key='', body=json.dumps(data))
    
    def slave_to_master(self):
        self.type = "master"
        self.thread = threading.Thread(target=self.master_target, args=())
        self.thread.start()




    def run(self):
        self.thread.start()


# global object for masterSlave class
lol = masterSlave()


def receiveSignal2(signalNumber, frame):
    """
        On recieving SIGTERM delete master node
        and stop this container.
    """
    global notDead
    notDead = False
    pid = this.attrs['State']['Pid']
    zk.delete('/master/'+str(pid))
    time.sleep(1)
    this.stop()
    return

    

def receiveSignal(signalNumber, frame):
    """
        On recieving SIGTERM convert slave to master
        by removing slave node and creating master
        node.
        and stop this container.
    """
    global notDead
    if(notDead):
        global lol
        global this
        pid = this.attrs['State']['Pid']
        zk.create('/master/'+ str(pid), this.id.encode())
        lol.slave_to_master()
        signal.signal(signal.SIGTERM, receiveSignal2)
        zk.delete('/slave/'+str(pid))
        time.sleep(1)
        return
    else:
        exit()


def receiveSignal3(signalNumber, frame):
    """
        On recieving SIGQUIT delete slave node
        and stop this container.
    """
    global notDead
    notDead = False
    pid = this.attrs['State']['Pid']
    zk.delete('/slave/'+ str(pid))
    time.sleep(1)
    this.stop()
    return

    

def exitfunc():
    """
        If any other error occurs,
        Run functions so that node is deleted before 
        container is stopped.
    """
    global lol
    if lol.type == "master":
        receiveSignal2(1,2)
    else:
        receiveSignal3(1,2)




if __name__ == '__main__':

    # get PID of current program
    pid = this.attrs['State']['Pid']

    # create a slave node
    zk.create('/slave/'+ str(pid), this.id.encode())

    # Handling SIGTERM signal
    signal.signal(signal.SIGTERM, receiveSignal)

    # Handling SIGQUIT signal
    signal.signal(signal.SIGQUIT, receiveSignal3)

    # Handling any occurence of error
    atexit.register(exitfunc)

    # Run the slave
    lol.run()

