import re
import json
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, abort, Response

app = Flask(__name__)

# Working
# Add a new user to the database
@app.route('/api/v1/users', methods=['PUT'])
def add_user():
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
	response = requests.post(url='http://localhost:8080/api/v1/db/read', json={'api':'add_user', 'username':username})
	if (response.json())['user_exists']:
		# User already exists in the database
		return jsonify({"error":"user already exists"}), 400

	# Insert the user into the database
	response = requests.post(url='http://localhost:8080/api/v1/db/write', json={'api':'add_user', 'username':username, 'password':password})
	return jsonify(response.json()), 201

# Working
# Delete an existing user from the database
@app.route('/api/v1/users/<string:username>', methods=['DELETE'])
def delete_user(username):
	# Print the input data to verify format
	print("\n\n\n\n\n\n\n\nCalled delete_user API")
	print(username, "\n\n\n\n\n\n\n\n")

	# Check if user exists in the database
	response = requests.post(url='http://localhost:8080/api/v1/db/read', json={'api':'delete_user', 'username':username})
	if not (response.json())['user_exists']:
		# User not in the database
		return jsonify({'error':'user not in database'}), 400

	# Remove the user from the database
	response = requests.post(url='http://localhost:8080/api/v1/db/write', json={'api':'delete_user', 'username':username})
	return jsonify(response.json()), 200

# Working
# List all existing users in the database
@app.route('/api/v1/users', methods=['GET'])
def list_users():
	# Print the input data to verify format
	print("\n\n\n\n\n\n\n\nCalled list_users API\n\n\n\n\n\n\n\n")

	# Check if user exists in the database
	response = requests.post(url='http://localhost:8080/api/v1/db/read', json={'api':'list_users'})
	if not (response.json()):
		# No users in the database
		return jsonify(response.json()), 204

	# Return
	return jsonify(response.json()), 200

# Working
# Delete an existing user from the database
@app.route('/api/v1/db/clear', methods=['POST'])
def db_clear():
	# Print the API called
	print("\n\n\n\n\n\n\n\nCalled delete users database API\n\n\n\n\n\n\n\n")

	# Clear the user database
	requests.post(url='http://localhost:8080/api/v1/db/write', json={'api':'db_clear'})

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
		requests.post(url='http://172.17.0.1:8000/api/v1/db/write', json={'api':'delete_user', 'username':username})

		# Remove user form the user database
		users_data = pd.read_csv('users.csv')
		users_data = users_data[users_data.username != username]
		users_data.to_csv('users.csv', index=False)

		return jsonify({}), 200

	# If the calling API is db_clear API
	if data['api'] == 'db_clear':
		# Clear the rides database
		requests.post(url='http://172.17.0.1:8000/api/v1/db/clear')

		# Clear the users database
		users = pd.DataFrame({'username':[], 'password':[]})
		users.to_csv('users.csv', index=False)

		return jsonify({}), 200

@app.route('/api/v1/db/read', methods=['POST'])
def db_read():
	# Extract the json data
	data = request.get_json()

	# If the calling API is add_user API
	if data['api'] == 'add_user':
		return_data = dict()

		# Extract users from the users database
		response = requests.get(url='http://localhost:8080/api/v1/users')

		try:
			existing_users = list(map(str, response.json()))
			# Check if user exists in the database
			if data['username'] in list(existing_users):
				return_data['user_exists'] = True
			else:
				return_data['user_exists'] = False

		except ValueError:
			return_data['user_exists'] = False

		return jsonify(return_data), 200

	# If the calling API is delete_user API
	if data['api'] == 'delete_user':
		return_data = dict()

		# Extract users from the users database
		response = requests.get(url='http://localhost:8080/api/v1/users')

		try:
			existing_users = list(map(str, response.json()))
			# Check if user exists in the database
			if data['username'] in list(existing_users):
				return_data['user_exists'] = True
			else:
				return_data['user_exists'] = False

		except ValueError:
			return_data['user_exists'] = False

		return jsonify(return_data), 200

	# If the calling API is list_users API
	if data['api'] == 'list_users':
		# Extract users from the users database
		existing_users = pd.read_csv('users.csv')['username']
		existing_users = list(map(str, existing_users))

		return jsonify(existing_users), 200

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=8080)
