
# coding: utf-8

# # This is a capstone notebook

# In[1]:


import pandas as pd


# ### Import the requests package to read the wiki page from URL

# In[3]:


import requests

url = "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M"
page = requests.get(url)
print (page.status_code) # this hsoud print 200


# ### Import the BeautifulSoap package to scrape the page

# In[4]:


# !conda install -c anaconda beautifulsoup4 #import beatiful soap 
from bs4 import BeautifulSoup

soup = BeautifulSoup(page.content, 'html.parser')


# #### Find the table wich contains the postal code and the neighbourhood data

# In[30]:


tb = soup.find('table', class_='wikitable sortable')


# #### Parse the Postal Code, Borough and Neighbourhood from the table and store it to a list

# In[31]:


postal_codes = []

for tr in tb.find_all('tr'):
    lst = ""
    for td in tr.find_all('td'):
        lst = lst + td.get_text().strip('\n') + ','
    
    # Add only those entries for which the Borough does not contain Not assigned
    if lst.strip().strip('\n') and not lst.split(',')[1].__contains__("Not assigned"):
        entry = lst.split(',')[0:3]
        if len(postal_codes) ==0:
            postal_codes.append(entry)
        else:
            exists = False
            # If there is already an entry in the list then update the entry by appending the Neighbourhood to the list
            for pc in postal_codes:
                if pc[0] == entry[0] and pc[1] == entry[1]:
                    pc[2] = pc[2]+', '+entry[2]
                    exists = True
                    break
            if not exists:
                # if the neighbourhood contains Not assigned then replace it with the value of Borough
                if entry[2].__contains__("Not assigned"):
                    entry[2] = entry[1]
                postal_codes.append(entry)


# Create a data frame of the data

# In[49]:


df_postal = pd.DataFrame(postal_codes, columns = ['PostCode', 'Borough', 'Neighbourhood'])
df_postal


# Display the shape of teh data frame

# In[35]:


df_postal.shape


# In[44]:


#!conda install -c conda-forge geopy --yes # uncomment this line if you haven't completed the Foursquare API lab
from geopy.geocoders import Nominatim # convert an address into latitude and longitude values


# In[48]:


file_name = 'http://cocl.us/Geospatial_data/Geospatial_Coordinates.csv'
df_geospatial = pd.read_csv(file_name)
df_geospatial


# In[54]:


df_merged = pd.merge(left=df_postal,right=df_geospatial, left_on='PostCode', right_on='Postal Code')
df_merged = df_merged[df_merged.columns.intersection(['PostCode', 'Borough', 'Neighbourhood', 'Latitude', 'Longitude'])]
df_merged


# In[60]:


print('The dataframe has {} boroughs and {} neighborhoods.'.format(
        len(df_merged['Borough'].unique()),
        df_merged.shape[0]
    )
)


# In[58]:


import folium
# create map of Toronto using latitude and longitude values
map_toronto = folium.Map(location=[43.6, -79.3], zoom_start=10)

# add markers to map
for lat, lng, borough, neighborhood in zip(df_merged['Latitude'], df_merged['Longitude'], df_merged['Borough'], df_merged['Neighbourhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='orange',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_toronto)  
    
map_toronto


# #### Lets the North York Borough

# In[61]:


northyork_data = df_merged[df_merged['Borough'] == 'North York'].reset_index(drop=True)
northyork_data.head()


# In[62]:


# create map of Manhattan using latitude and longitude values
map_northyork = folium.Map(location=[43.7, -79.4], zoom_start=11)

# add markers to map
for lat, lng, label in zip(northyork_data['Latitude'], northyork_data['Longitude'], northyork_data['Neighbourhood']):
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='red',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_northyork)  
    
map_northyork


# #### Define Foursquare Credentials and Version

# In[59]:


CLIENT_ID = 'YOB2WKHROLSVRS3IKPKX0GNLHNPL4PAD5HZ3W1L0DUTBJ4CQ' # your Foursquare ID
CLIENT_SECRET = 'DWCUU1QM4EK2GHZKMMJ0QSNUGDCJM221BVL1ZXKVZACR4I3O' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version

print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# #### Let's explore the first neighborhood in our dataframe. Get the latitude, longitude 

# In[66]:


northyork_data.loc[0, 'Neighbourhood']
neighborhood_latitude = northyork_data.loc[0, 'Latitude'] # neighborhood latitude value
neighborhood_longitude = northyork_data.loc[0, 'Longitude'] # neighborhood longitude value

neighborhood_name = northyork_data.loc[0, 'Neighbourhood'] # neighborhood name

print('Latitude and longitude values of {} are {}, {}.'.format(neighborhood_name, 
                                                               neighborhood_latitude, 
                                                               neighborhood_longitude))


# #### Now, let's get the top 100 venues that are in Parkwoods within a radius of 700 meters.

# In[67]:


LIMIT = 100 # limit of number of venues returned by Foursquare API
radius = 500 # define radius
# create URL
url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    neighborhood_latitude, 
    neighborhood_longitude, 
    radius, 
    LIMIT)
url # display URL


# #### Call the Get method and check the results

# In[68]:


results = requests.get(url).json()
results


# In[69]:


# function that extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# Now we are ready to clean the json and structure it into a *pandas* dataframe.

# In[71]:


venues = results['response']['groups'][0]['items']
    
nearby_venues = json_normalize(venues) # flatten JSON

# filter columns
filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
nearby_venues =nearby_venues.loc[:, filtered_columns]

# filter the category for each row
nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

# clean columns
nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

nearby_venues.head()

print('{} venues were returned by Foursquare.'.format(nearby_venues.shape[0]))


# ## Explore Neighborhoods in North York

# #### Let's create a function to repeat the same process to all the neighborhoods in North York

# In[73]:


def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighbourhood', 
                  'Neighbourhood Latitude', 
                  'Neighbourhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[74]:


# call the above function

northyork_venues = getNearbyVenues(names=northyork_data['Neighbourhood'],
                                   latitudes=northyork_data['Latitude'],
                                   longitudes=northyork_data['Longitude']
                                  )


# In[75]:


print(northyork_venues.shape)
northyork_venues.head()


# In[76]:


# Let's check how many venues were returned for each neighborhood

northyork_venues.groupby('Neighbourhood').count()


# In[77]:


# Let's find out how many unique categories can be curated from all the returned venues

print('There are {} uniques categories.'.format(len(northyork_venues['Venue Category'].unique())))


# ## Analyze Each Neighborhood

# In[83]:


# one hot encoding
northyork_onehot = pd.get_dummies(northyork_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
northyork_onehot['Neighbourhood'] = northyork_venues['Neighbourhood'] 

# move neighborhood column to the first column
fixed_columns = [northyork_onehot.columns[-1]] + list(northyork_onehot.columns[:-1])
northyork_onehot = northyork_onehot[fixed_columns]

northyork_onehot.shape


# #### Next, let's group rows by neighborhood and by taking the mean of the frequency of occurrence of each category

# In[85]:


northyork_grouped = northyork_onehot.groupby('Neighbourhood').mean().reset_index()
northyork_grouped.shape


# Let's print each neighborhood along with the top 5 most common venues

# In[114]:


num_top_venues = 5

for hood in northyork_grouped['Neighbourhood']:
    print("----"+hood+"----")
    temp = northyork_grouped[northyork_grouped['Neighbourhood'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# In[115]:


# write a function to sort the venues in descending order
def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# In[122]:


#create the new dataframe and display the top 10 venues for each neighborhood.

num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighbourhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighbourhood'] = northyork_grouped['Neighbourhood']

for ind in np.arange(northyork_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(northyork_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# ### K-Means Clustering

# In[123]:


# set number of clusters
kclusters = 4

northyork_grouped_clustering = northyork_grouped.drop('Neighbourhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(northyork_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10] 


# create a new dataframe that includes the cluster as well as the top 10 venues for each neighborhood.

# In[124]:


# add clustering labels
neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

ny_merged = northyork_data

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
ny_merged = ny_merged.join(neighborhoods_venues_sorted.set_index('Neighbourhood'), on='Neighbourhood')

ny_merged # check the last columns!


# Visualizing the results

# In[125]:


# create map
map_clusters = folium.Map(location=[43.7, -79.4], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(ny_merged['Latitude'], ny_merged['Longitude'], ny_merged['Neighbourhood'], ny_merged['Cluster Labels'].fillna(0).astype(int)):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster-1],
        fill=True,
        fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# ## Examining Clusters

# In[127]:


# Cluster 1
ny_merged.loc[ny_merged['Cluster Labels'] == 0, ny_merged.columns[[1] + list(range(5, ny_merged.shape[1]))]]


# In[128]:


# Cluster 2
ny_merged.loc[ny_merged['Cluster Labels'] == 1, ny_merged.columns[[1] + list(range(5, ny_merged.shape[1]))]]


# In[130]:


# Cluster 3
ny_merged.loc[ny_merged['Cluster Labels'] == 2, ny_merged.columns[[1] + list(range(5, ny_merged.shape[1]))]]


# In[131]:


# Cluster 4
ny_merged.loc[ny_merged['Cluster Labels'] == 3, ny_merged.columns[[1] + list(range(5, ny_merged.shape[1]))]]


# ## Observations - Cluster 1 has 1, Cluster 2 has 24, Cluster 3 has 2 and Cluster 4 has 2
