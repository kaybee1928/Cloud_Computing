Contents of this directory:

1. rides directory - 	all the necessary stuff for the rides microservice including the
			Dockerfile and docker-compose.yml files.
2. users directory - 	all the necessary stuff for the users microservice including the
			Docekrfile and docker-compose.yml files.
3. CC_0129_0837_1525_rides.py - python code for all the rides microcervice APIs.
4. CC_0129_0837_1525_users.py - python code for all the users microservice APIS.


How to use:

1. Create a t2.micro EC2 instance in AWS
2. install docker and docker-compose
3. change the IP addresses in the codes as per the deployment
4. cd into the respective microservice directories
5. build the docker-compose images using the command 'sudo docker-compose build'
6. start the docker images using the command 'sudo docker-compose up'
7. To stop any of the microservices use the command 'sudo docker-compose down'
