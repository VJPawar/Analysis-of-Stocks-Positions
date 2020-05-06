#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 17:15:45 2019

@author: nikhildikshit
"""

import pandas as pd 
import matplotlib.pyplot as plt
import folium
from collections import Counter
from geopy import GoogleV3
print("\n")

# PART 1
# reading start.csv, trades.csv, and table.html into Pandas.
startDf = pd.read_csv("start.csv", names=['Symbol', 'Stock Position']) 
print("start.csv read successfully! \n")
tradesDf = pd.read_csv("trades.csv", names=['Symbol', 'Stock Position'])
print("start.csv read successfully! \n")
tableDf = pd.read_html('table.html')[0]
print("table.html read successfully! \n")
tableDf.to_csv("table.csv", sep=',', header = None)
print("table.html converted to table.csv for future use")

# PART 2
""" 
calculating the sum of number of trades for all instances of every respective Symbol
this is not required for start.csv but doing that here, just in case
"""
tradesGroupedTotal = tradesDf.groupby(['Symbol']).sum()
startDfGroupedTotal = startDf.groupby(['Symbol']).sum()

# this sums the start of day portfolio with the trades that have occurred during the day
eodDf = startDfGroupedTotal.groupby('Symbol').sum().add(tradesGroupedTotal.groupby('Symbol').sum(), fill_value=0).reset_index()
eodDf.to_csv("eod.csv", sep=',', index = False, header = None)
print("\nHead of eod.csv: ")
print(eodDf.head())

# PART 3
# creating dataframe from the table.html
tableDf = tableDf.loc[:, ["Symbol","GICS Sector"]]
merged = pd.merge(tableDf, eodDf, on="Symbol")
merged = merged.loc[:, ["GICS Sector", "Stock Position"]]

# adding the number of trades for all symbols in a sector
sectorsTable = merged.groupby("GICS Sector").sum()
sectorsTable.to_csv("sector.csv", sep=',', header = None)
print("\nHead of sector.csv: ")
print(sectorsTable.head())

# PART 4
"""
I do 2 things.
1. We can do some analysis to visualize the distribution of each 'Sector' or 'State' etc.
2. We can generate a pretty map to plot the headquarters locations in the dataset (used google api to do this)
"""
fullTableDf = pd.read_csv("table.csv", names=['Symbol',
                                            'Security', 
                                            'SEC Filing', 
                                            'Sector', 
                                            'Sub Industry',
                                            'Address', 
                                            'DateAdded', 
                                            'CIK', 
                                            'Founded'])

# seperating city and state from address to do further fact-based quantitative analysis 
address = fullTableDf["Address"].str.split(", ", n = 1, expand = True) 
fullTableDf["City"]= address[0] 
fullTableDf["State"]= address[1] 
fullTableDf = fullTableDf.loc[:, ["Symbol", "Address", 'City', 'State', 'DateAdded', 'Sector']]


# GENERATING THE MAP OF OUR HEADQUARTERS
# creating a smaller dataframe here because the complete dataframe is huge and my API times out before iterating over all entries
# 150 rows are chosen fom the beginning to plot on the map
# results will be similar on the complete dataset if we upgrade our API
smallDf = fullTableDf.iloc[:150]
print("\nHead of the smaller dataframe for plotting the map: ")
print(smallDf.head())

geocode = GoogleV3('AIzaSyDNqc0tWzXHx_wIp1w75-XTcCk4BSphB5w').geocode 
addresses = smallDf['Address'].tolist()

# generating latitudes and longitudes of all the HQ addresses in the dataset
print("\n\nPlease wait... generating coordinates for our map! It takes some time.\n")
latitudes = []
longitudes = []
for address in addresses:
        x = geocode(address)
        latitudes.append(x.latitude)
        longitudes.append(x.longitude)

smallDf['Latitude'] = pd.DataFrame({'Latitude': latitudes})
smallDf['Longitude'] = pd.DataFrame({'Longitude': longitudes})
print("\nColumns in the small dataframe after adding the coordinates: ")
print(smallDf.columns)

# using generated coordiinates to plot our pretty map 
def generateMap():
    myMap = folium.Map(location=[37.0902, -95.7129], zoom_start = 5)
    for lat, lon, city, founded, sector in zip(smallDf['Latitude'], smallDf['Longitude'], smallDf['City'], smallDf['DateAdded'], smallDf['Sector'],):
        folium.Marker(
            [lat, lon],
            popup = ('City: ' + str(city).capitalize() + '<br>'
                     'Date First Added: ' + str(founded) + '<br>'
                     'Sector: ' + str(sector)),
            fill=True,
            radius=12,
            threshold_scale=[0,1,2,3],
            fill_opacity=0.7,
            max_width=450
            ).add_to(myMap)
    myMap.save("myMap.html")

# a litle python magic to generate graphs for the top 10 sectors or states etc. with their overall distribution 
def sectorDistribution(feature):
    c = Counter(feature)
    histo = c.most_common(10)
    freq = {}
    for item,count in histo:
        freq[item]=count
    explode = (0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05)
    plt.pie([float(v) for v in freq.values()], labels = [(k) for k in freq],
               autopct = '%.2f',startangle = 90, pctdistance = 0.85, explode = explode, radius = 3, textprops={'fontsize': 14})
    centre_circle = plt.Circle((0, 0), 0.90, fc = 'white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.tight_layout()
    plt.show()

generateMap()
print("\nHTML for the map is created!\n")
print("\nNow... creating exciting graphs to see it all!\n")
print("\nDistribution of all the sectors: ")
sectorDistribution(fullTableDf.Sector)
print("\nDistribution of all the states: ")
sectorDistribution(fullTableDf.State)


