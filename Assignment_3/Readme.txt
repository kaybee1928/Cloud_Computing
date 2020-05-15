Contents of this directory:

1. rides directory - 	all the necessary stuff for the rides microservice including the
			Dockerfile and docker-compose.yml files.
2. users directory - 	all the necessary stuff for the users microservice including the
			Docekrfile and docker-compose.yml files.
3. CC_0129_0837_1525_rides.py - python code for all the rides microcervice APIs
4. CC_0129_0837_1525_users.py - python code for all the users microservice APIS


How to use:

1. Create two t2.micro EC2 instance in AWS
2. create two target groups for each of the instances
3. deploy the two instances over a load balancer with the correct paths configured
4. install docker and docker-compose on both the instances
5. change the IP addresses and ports in the code as required by the architecture
5. cd into the respective microservice directories on each instance
6. build the docker-compose images using the command 'sudo docker-compose build' on both instances
7. start the docker images using the command 'sudo docker-compose up' on both instances
8. To stop any of the microservices use the command 'sudo docker-compose down' instances
