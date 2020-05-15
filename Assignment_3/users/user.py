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
	requests.get(url='http://0.0.0.0:80/api/v1/_count_increment')
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
	response = requests.post(url='http://0.0.0.0:80/api/v1/db/read', json={'api':'add_user', 'username':username})
	if (response.json())['user_exists']:
		# User already exists in the database
		return jsonify({"error":"user already exists"}), 400

	# Insert the user into the database
	response = requests.post(url='http://0.0.0.0:80/api/v1/db/write', json={'api':'add_user', 'username':username, 'password':password})
	return jsonify(response.json()), 201

# Working
# Delete an existing user from the database
@app.route('/api/v1/users/<string:username>', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def delete_user(username):
	requests.get(url='http://0.0.0.0:80/api/v1/_count_increment')
	if request.method != 'DELETE':
		return jsonify({'error':'wrong method used'}), 405

	# Print the input data to verify format
	print("\n\n\n\n\n\n\n\nCalled delete_user API")
	print(username, "\n\n\n\n\n\n\n\n")

	# Check if user exists in the database
	response = requests.post(url='http://0.0.0.0:80/api/v1/db/read', json={'api':'delete_user', 'username':username})
	if not (response.json())['user_exists']:
		# User not in the database
		return jsonify({'error':'user not in database'}), 400

	# Remove the user from the database
	response = requests.post(url='http://0.0.0.0:80/api/v1/db/write', json={'api':'delete_user', 'username':username})
	return jsonify(response.json()), 200

# Working
# List all existing users in the database
@app.route('/api/v1/users', methods=['GET', 'HEAD', 'POST', 'DELETE'])
def list_users():
	requests.get(url='http://0.0.0.0:80/api/v1/_count_increment')
	if request.method != 'GET':
		return jsonify({'error':'wrong method used'}), 405

	# Print the input data to verify format
	print("\n\n\n\n\n\n\n\nCalled list_users API\n\n\n\n\n\n\n\n")

	# Check if user exists in the database
	response = requests.post(url='http://0.0.0.0:80/api/v1/db/read', json={'api':'list_users'})
	if not (response.json()):
		# No users in the database
		return jsonify(response.json()), 204

	# Return
	return jsonify(response.json()), 200

# Working
# Delete an existing user from the database
@app.route('/api/v1/db/clear', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def db_clear():
	#requests.get(url='http://0.0.0.0:80/api/v1/_count_increment')
	if request.method != 'POST':
		return jsonify({'error':'wrong method used'}), 405

	# Print the API called
	print("\n\n\n\n\n\n\n\nCalled delete users database API\n\n\n\n\n\n\n\n")

	# Clear the user database
	requests.post(url='http://0.0.0.0:80/api/v1/db/write', json={'api':'db_clear'})

	# Return
	return jsonify({}), 200

@app.route('/api/v1/_count', methods=['GET', 'HEAD', 'POST', 'PUT'])
def get_request_count():
	if request.method != 'GET':
		return jsonify({'error':'wrong method used'}), 405

	# Print the API called
	print("\n\n\n\n\n\n\n\nCalled get_request_count API\n\n\n\n\n\n\n\n")

	# Obtain the number of http requests
	response = requests.post(url='http://0.0.0.0:80/api/v1/db/read', json={'api':'get_request_count'})
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
	requests.post(url='http://0.0.0.0:80/api/v1/db/write', json={'api':'reset_request_count'})

	# Return
	return jsonify({}), 200

@app.route('/api/v1/_count_increment', methods=['GET'])
def increment_request_count():
	# Print the API called
	print("\n\n\n\n\n\n\n\nCalled increment_request_count API\n\n\n\n\n\n\n\n")

	# Obtain the number of http requests
	requests.post(url='http://0.0.0.0:80/api/v1/db/write', json={'api':'increment_request_count'})

	# Return
	return jsonify({}), 200

@app.route('/api/v1/db/write', methods=['POST'])
def db_write():
	# Extract the json data
	data = request.get_json()

	# If the calling API is add_user API
	if data['api'] == 'add_user':
		username = data['username']
		password = data['password']

		# Add the user to the database
		users_data = pd.read_csv('users.csv')
		users_data = users_data.append({'username': username, 'password': password}, ignore_index=True)
		users_data.to_csv('users.csv', index=False)

		return jsonify({}), 201

	# If the calling API is delete_user API
	if data['api'] == 'delete_user':
		username = data['username']

		# Remove user data from rides database
		requests.post(url='http://3.82.251.34:80/api/v1/db/write', json={'api':'delete_user', 'username':username})

		# Remove user form the user database
		users_data = pd.read_csv('users.csv')
		users_data = users_data[users_data.username != username]
		users_data.to_csv('users.csv', index=False)

		return jsonify({}), 200

	# If the calling API is db_clear API
	if data['api'] == 'db_clear':
		# Clear the rides database
		requests.post(url='http://3.82.251.34:80/api/v1/db/write', json={'api':'db_clear'})

		# Clear the users database
		users = pd.DataFrame({'username':[], 'password':[]})
		users.to_csv('users.csv', index=False)

		return jsonify({}), 200

	if data['api'] == 'reset_request_count':
		# Reset the requests count
		rides_count = open('requests_count.txt','w')
		rides_count.write(str(0))
		rides_count.close()

		return jsonify({}), 200

	if data['api'] == 'increment_request_count':
		# Read the latest requests_count
		requests_count = open('requests_count.txt','r')
		last_requests_count = requests_count.read()
		requests_count.close()

		# Update the latest requests_count
		current_requests_count = int(last_requests_count) + 1
		requests_count = open('requests_count.txt','w')
		requests_count.write(str(current_requests_count))
		requests_count.close()

		return jsonify({}), 200

@app.route('/api/v1/db/read', methods=['POST'])
def db_read():
	# Extract the json data
	data = request.get_json()

	# If the calling API is add_user API
	if data['api'] == 'add_user':
		return_data = dict()

		# Extract users from the users database
		response = requests.post(url='http://0.0.0.0:80/api/v1/db/read', json={'api':'list_users'})

		if response.json():
			existing_users = list(map(str, response.json()))
			# Check if user exists in the database
			if data['username'] in list(existing_users):
				return_data['user_exists'] = True
			else:
				return_data['user_exists'] = False

		else:
			return_data['user_exists'] = False

		return jsonify(return_data), 200

	# If the calling API is delete_user API
	if data['api'] == 'delete_user':
		return_data = dict()

		# Extract users from the users database
		response = requests.post(url='http://0.0.0.0:80/api/v1/db/read', json={'api':'list_users'})

		if response.json():
			existing_users = list(map(str, response.json()))
			# Check if user exists in the database
			if data['username'] in list(existing_users):
				return_data['user_exists'] = True
			else:
				return_data['user_exists'] = False

		else:
			return_data['user_exists'] = False

		return jsonify(return_data), 200

	# If the calling API is list_users API
	if data['api'] == 'list_users':
		# Extract users from the users database
		existing_users = pd.read_csv('users.csv')['username']
		existing_users = list(map(str, existing_users))

		return jsonify(existing_users), 200

	if data['api'] == 'get_request_count':
		# Read the latest requests_count
		requests_count = open('requests_count.txt','r')
		last_requests_count = requests_count.read()
		requests_count.close()

		return json.dumps([int(last_requests_count)]), 200

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=80)
