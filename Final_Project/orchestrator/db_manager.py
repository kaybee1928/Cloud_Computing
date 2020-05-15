import pandas as pd 
  

# Remove all duplicates from users.csv file
data = pd.read_csv("users.csv") 
data.sort_values("username", inplace = True) 
data.drop_duplicates(subset ="username", 
                     keep = "first", inplace = True) 

data.to_csv("users.csv", index=False)



# Remove all duplicates from rides.csv file
data = pd.read_csv("rides.csv") 
data.sort_values("rideId", inplace = True) 
data.drop_duplicates(subset ="rideId", 
                     keep = "first", inplace = True) 
data.to_csv("rideId.csv", index=False)