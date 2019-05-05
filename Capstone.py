
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

# In[34]:


df_postal = pd.DataFrame(postal_codes, columns = ['Postcode', 'Borough', 'Neighbourhood'])
df_postal


# Display the shape of teh data frame

# In[35]:


df_postal.shape

