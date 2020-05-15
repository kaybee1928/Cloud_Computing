import re
import json
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, abort, Response

app = Flask(__name__)

# Working
# Create a new ride in the database
@app.route('/api/v1/rides', methods=['HEAD', 'POST', 'PUT', 'DELETE'])
def new_ride():
    requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'POST':
        return jsonify({'error':'wrong method used'}), 405

    # Obtain the data in json format
    data = request.get_json()
    keys = data.keys()

    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled new_ride API")
    print(data, "\n\n\n\n\n\n\n\n")

    # Verify the format of the data
    if 'created_by' not in keys or 'timestamp' not in keys or 'source' not in keys or 'destination' not in keys:
        return jsonify({'error':'wrong json format'}), 400

    # Obtain the ride information form the json
    created_by = str(data['created_by'])
    timestamp = str(data['timestamp'])
    source = int(data['source'])
    destination = int(data['destination'])

    # Verify the source and destination for validity
    if source == destination:
        return jsonify({'error':'source is same as destination'}), 400

    # Verify the timestamp
    try:
        datetime.strptime(timestamp, '%d-%m-%Y:%S-%M-%H')
    except ValueError:
        return jsonify({'error':'invalid timestamp'}), 400

    # Verify the format of the timestamp
    date, month, year = (timestamp.split(':')[0]).split('-')
    second, minute, hour = (timestamp.split(':')[1]).split('-')
    if len(date) is not 2 or len(month) is not 2 or len(year) is not 4 or len(second) is not 2 or len(minute) is not 2 or len(hour) is not 2:
        return jsonify({'error':'wrong timestamp length/format'}), 400

    # Check the timestamp to verify that the ride is scheduled in the future
    ride_time = datetime.strptime(timestamp, '%d-%m-%Y:%S-%M-%H')
    current_time = datetime.now()
    if (ride_time-current_time).total_seconds() < 0:
        return jsonify({'error':'time is in the past'}), 400

    # Validate the source, destination and username
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'new_ride', 'username':created_by, 'source':source, 'destination':destination})
    if not (response.json())['source_exists']:
        return jsonify({'error':'source not in database'}), 400
    if not (response.json())['destination_exists']:
        return jsonify({'error':'destination not in database'}), 400
    if not (response.json())['user_exists']:
        return jsonify({'error':'user not in database'}), 400

    # Insert ride details into the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'new_ride', 'created_by':created_by, 'timestamp':timestamp, 'source':source, 'destination':destination})
    return jsonify(response.json()), 201

# Working
# List all the rides from a given source to given destination
@app.route('/api/v1/rides', methods=['GET', 'HEAD', 'PUT', 'DELETE'])
def list_rides():
    requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'GET':
        return jsonify({'error':'wrong method used'}), 405

    # Ontain the data
    source = request.args.get('source')
    destination = request.args.get('destination')
    none_type = request.args.get('none_type')

    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled list_rides API")
    print(source, destination, "\n\n\n\n\n\n\n\n")

    # Check if source and destination is present
    if source is none_type or destination is none_type or (not source.isdigit()) or (not destination.isdigit()):
        return jsonify({'error':'source or destination is missing'}), 400

    # Obtain the source and the destination
    source = int(request.args.get('source'))
    destination = int(request.args.get('destination'))

    # Read the database for the rides and return 204 if not ride found
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'list_rides', 'source':source, 'destination':destination})
    if not response.json():
        return jsonify(), 204

    return jsonify(response.json()), 200

# Working
# Return the details of a particular ride
@app.route('/api/v1/rides/<int:rideId>', methods=['GET', 'HEAD', 'PUT'])
def get_ride_details(rideId):
    requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'GET':
        return jsonify({'error':'wrong method used'}), 405

    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled get_ride_details API")
    print(rideId, "\n\n\n\n\n\n\n\n")

    # Read the database for the ride details
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'get_ride_details', 'rideId':rideId})

    # If there is not ride with the specified rideId
    if not response.json():
        return jsonify({'error':'no ride with specified rideId'}), 400

    return jsonify(response.json()), 200

# Working
# Adding a user to an existing ride
@app.route('/api/v1/rides/<int:rideId>', methods=['HEAD', 'POST', 'PUT'])
def join_ride(rideId):
    requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'POST':
        return jsonify({'error':'wrong method used'}), 405

    # Obtain the data in json format
    data = request.get_json()
    keys = data.keys()

    print("\n\n\n\n\n\n\n\nCalled join_ride API")
    print(rideId, data, "\n\n\n\n\n\n\n\n")

    # Verify the format of the data
    if 'username' not in keys:
        # Json is invalid
        return jsonify({'error':'wrong json format'}), 400

    # Obtain the username from the json
    username = str(data['username'])

    # Read the database to check if user exists, ride exists and if it is expired or not
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'join_ride', 'username':username, 'rideId':rideId})
    if not (response.json())['user_exists']:
        return jsonify({'error':'user not in database'}), 400
    if not (response.json())['rideId_exists']:
        return jsonify({'error':'rideId not in database'}), 400
    if not (response.json())['ride_valid']:
        return jsonify({'error':'ride is expired'}), 400
    if not (response.json())['can_add_rider']:
        return jsonify({'error':'rider already in ride'}), 400

    # Add new user to the ride
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'join_ride', 'username':username, 'rideId':rideId})
    return jsonify(response.json()), 201

# Working
# Deleting a ride from the database
@app.route('/api/v1/rides/<int:rideId>', methods=['HEAD', 'PUT', 'DELETE'])
def delete_ride(rideId):
    requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'DELETE':
        return jsonify({'error':'wrong method used'}), 405
    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled delete_ride API")
    print(rideId, "\n\n\n\n\n\n\n\n")

    # Check if the rideId exists in the database and if not return error
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'delete_ride', 'rideId':rideId})
    if not (response.json())['rideId_exists']:
        return jsonify({'error':'rideId not in the database'}), 400

    # Remove ride from the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'delete_ride', 'rideId':rideId})
    return jsonify(response.json()), 200

@app.route('/api/v1/rides/count', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def count_rides():
    requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'GET':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled count_rides API\n\n\n\n\n\n\n\n")

    # Clear the rides database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'count_rides'})

    # Return
    return jsonify(response.json()), 200

# Working
# Delete an existing user from the database
@app.route('/api/v1/db/clear', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def db_clear():
    #requests.get(url='http://ec2-3-221-198-97.compute-1.amazonaws.com/api/v1/increment_rides_api_request_count')
    if request.method != 'POST':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled delete rides database API\n\n\n\n\n\n\n\n")

    # Clear the rides database
    requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'rides_db_clear'})

    # Return
    return jsonify({}), 200

@app.route('/api/v1/_count', methods=['GET', 'HEAD', 'POST', 'PUT'])
def get_request_count():
    if request.method != 'GET':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled get_request_count API\n\n\n\n\n\n\n\n")

    # Obtain the number of http requests
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'get_rides_api_request_count'})

    # Return
    return jsonify(response.json()), 200

@app.route('/api/v1/_count', methods=['HEAD', 'POST', 'PUT', 'DELETE'])
def reset_request_count():
    if request.method != 'DELETE':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled reset_request_count API\n\n\n\n\n\n\n\n")

    # Obtain the number of http requests
    requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'reset_rides_api_request_count'})

    # Return
    return jsonify({}), 200

@app.route('/api/v1/increment_rides_api_request_count', methods=['GET'])
def increment_request_count():
    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled increment_request_count API\n\n\n\n\n\n\n\n")

    # Obtain the number of http requests
    requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'increment_rides_api_request_count'})

    # Return
    return jsonify({}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
