import re
import json
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, abort, Response

app = Flask(__name__)

# Working
# Add a new user to the database
@app.route('/api/v1/users', methods=['HEAD', 'POST', 'PUT', 'DELETE'])
def add_user():
    requests.get(url='http://ec2-18-213-147-182.compute-1.amazonaws.com/api/v1/increment_users_api_request_count')
    if request.method != 'PUT':
        return jsonify({'error':'wrong method used'}), 405

    # Obtain the data in json format
    data = request.get_json()
    keys = data.keys()

    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled add_user API")
    print(data, "\n\n\n\n\n\n\n\n")

    # Verify the format of the data
    if 'username' not in keys or 'password' not in keys:
        # Json is invalid
        return jsonify({'error':'wrong json format'}), 400

    # Obtain the username and password form the json
    username = str(data['username'])
    password = str(data['password'])

    # Verify the password format
    if len(password) is not 40 or not re.match(re.compile(r'\b[0-9a-f]{40}\b'), password):
        # Password is in wrong format
        return jsonify({'error':'wrong password format'}), 400

    # Check if username already exists in the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'add_user', 'username':username})
    if (response.json())['user_exists']:
        # User already exists in the database
        return jsonify({"error":"user already exists"}), 400

    # Insert the user into the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'add_user', 'username':username, 'password':password})
    return jsonify(response.json()), 201

# Working
# Delete an existing user from the database
@app.route('/api/v1/users/<string:username>', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def delete_user(username):
    requests.get(url='http://ec2-18-213-147-182.compute-1.amazonaws.com/api/v1/increment_users_api_request_count')
    if request.method != 'DELETE':
        return jsonify({'error':'wrong method used'}), 405

    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled delete_user API")
    print(username, "\n\n\n\n\n\n\n\n")

    # Check if user exists in the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'delete_user', 'username':username})
    if not (response.json())['user_exists']:
        # User not in the database
        return jsonify({'error':'user not in database'}), 400

    # Remove the user from the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'delete_user', 'username':username})
    return jsonify(response.json()), 200

# Working
# List all existing users in the database
@app.route('/api/v1/users', methods=['GET', 'HEAD', 'POST', 'DELETE'])
def list_users():
    requests.get(url='http://ec2-18-213-147-182.compute-1.amazonaws.com/api/v1/increment_users_api_request_count')
    if request.method != 'GET':
        return jsonify({'error':'wrong method used'}), 405

    # Print the input data to verify format
    print("\n\n\n\n\n\n\n\nCalled list_users API\n\n\n\n\n\n\n\n")

    # Check if user exists in the database
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'list_users'})
    if not (response.json()):
        # No users in the database
        return jsonify(response.json()), 204

    # Return
    return jsonify(response.json()), 200

# Working
# Delete an existing user from the database
@app.route('/api/v1/db/clear', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def db_clear():
    #requests.get(url='http://ec2-18-213-147-182.compute-1.amazonaws.com/api/v1/increment_users_api_request_count')
    if request.method != 'POST':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled delete users database API\n\n\n\n\n\n\n\n")

    # Clear the user database
    requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'users_db_clear'})

    # Return
    return jsonify({}), 200

@app.route('/api/v1/_count', methods=['GET', 'HEAD', 'POST', 'PUT'])
def get_request_count():
    if request.method != 'GET':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled get_request_count API\n\n\n\n\n\n\n\n")

    # Obtain the number of http requests
    response = requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/read', json={'api':'get_users_api_request_count'})
    print(response.json())

    # Return
    return jsonify(response.json()), 200

@app.route('/api/v1/_count', methods=['HEAD', 'POST', 'PUT', 'DELETE'])
def reset_request_count():
    if request.method != 'DELETE':
        return jsonify({'error':'wrong method used'}), 405

    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled reset_request_count API\n\n\n\n\n\n\n\n")

    # Obtain the number of http requests
    requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'reset_users_api_request_count'})

    # Return
    return jsonify({}), 200

@app.route('/api/v1/increment_users_api_request_count', methods=['GET'])
def increment_request_count():
    # Print the API called
    print("\n\n\n\n\n\n\n\nCalled increment_request_count API\n\n\n\n\n\n\n\n")

    # Obtain the number of http requests
    requests.post(url='http://ec2-3-210-229-6.compute-1.amazonaws.com/api/v1/db/write', json={'api':'increment_users_api_request_count'})

    # Return
    return jsonify({}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
