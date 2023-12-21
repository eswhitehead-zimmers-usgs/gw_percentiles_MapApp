# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 09:25:18 2023

@author: eswhitehead-zimmers
"""

import geopandas as gp
import folium as fl
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import plotly.express as px
from dataretrieval import nwis


def load_dat():
# This function loads in gw latlong 
    trends_all_sites = pd.read_csv(r"C:\Users\eswhitehead-zimmers\OneDrive - DOI\Documents\Python_Projects\percentile-trends\Data\trends_all_sites.csv")
    
    site_nos = trends_all_sites['site_no'].unique()
    
    return trends_all_sites, site_nos

def tidy_dat(trends_all_sites, all_sites):
# This function appends site names to the site number to allow for easier
# site selection
    
    # Convert all_sites to list of strings
    all_sites = list(map(str, all_sites))
    # pull site info for those sites
    siteINFO1 = nwis.get_info(sites = all_sites,
                              siteOutput = 'basic')
    # move site info to latlongframe
    pa_wells_info = siteINFO1[0]
    # Pull just station id and station name
    pa_wells_info = pa_wells_info[['site_no','station_nm','dec_lat_va','dec_long_va']]
    
    for name in pa_wells_info['station_nm']:
        words = name.split()
        whole_name =' '.join(words) 
        pa_wells_info['station_nm'][pa_wells_info['station_nm'] == name] = whole_name
     
    pa_wells_info = pa_wells_info.convert_dtypes()
    pa_wells_info['site_no'] = pd.to_numeric(pa_wells_info['site_no'])
    
    # Join station name to trends_all_sites by station id
    trends_names = pd.merge(trends_all_sites, pa_wells_info)
    
    return trends_names, pa_wells_info

def plot_dat(trends_name, station_nm):
# This function plots mann-kendall slope for each percentile of a given site
# Input:
    # trends_all_sites: variable containing all trends for all 76 sites
    # site_no: site number for the site you want trends plotted for. Note:
        # should be given as a string.
# Output:
    # plots trends for specified site_no
      
    # filter out which specific site you want to plot
    trends_name = trends_name[trends_name['station_nm'] == station_nm]
    
    # Create title including site no (which is variable)  
    titl_for_plot = 'Annual water level percentile trends for ' + station_nm
    
    # pretty close to final figure:
    fig = px.line(trends_name, y = 'slope', x = 'level_0', color = 'Trend')
    fig.update_traces(mode='markers')
    #fig.update_yaxes(range=[-6,6])
    fig.add_hline(y=0, line_width=3, line_dash="solid", line_color="green")
    fig.update_layout(
        title_text= titl_for_plot, 
        yaxis=dict(title='slope of trend (%)'),
        xaxis=dict(title='Groundwater Level Percentile'),
        autosize = False,
        width = 610,
        height = 480)

    return(fig)

def get_pos(lat, lng):
    return lat, lng
    
def getgeodf(pa_wells_info):
    
    df = pd.DataFrame(
        {
        "station_nm": [],
        "lat": [],
        "long": []
        }
    )
    
    for name in pa_wells_info["station_nm"]:
        df["station_nm"] = pa_wells_info["station_nm"]
        df["lat"] = pa_wells_info["dec_lat_va"]
        df["long"] = pa_wells_info["dec_long_va"]
    
    gdf = gp.GeoDataFrame(df,
                          geometry=gp.points_from_xy(df.long, df.lat),
                          crs=4326)
    
    return gdf

def choose_site(latlong, gdf):
    
    ### Make sure all the sites have the same precision for lat/long
    # Round data we have in geodataframe
    gdf.lat = gdf.lat.round(decimals = 4)
    gdf.long = gdf.long.round(decimals = 4)
    
    # Round latlong data from user
    # Put latlong into data frame so we have consistent rounding between user and gdf
    latlong_df = pd.DataFrame(
        {
        "lat": [latlong[0]],
        "long": [latlong[1]]
        }
    )
    
    # Round latlong
    latlong_df.lat = latlong_df.lat.round(decimals = 4)
    latlong_df.long = latlong_df.long.round(decimals = 4)
    
    
    # create counter variable for loop
    i = 0
    
    # Set option to zero for when user clicks a point that isn't a site
    option = 0

    
    for station_nm in gdf.station_nm:
        
        if (latlong_df.lat[0] == gdf["lat"][i] and latlong_df.long[0] == gdf["long"][i]):
            option = station_nm
        
        i = i + 1
        
    return option

### App Layout ###
# Adjust layout to take up full width of screen
st.set_page_config(layout="wide")

# Add Title
'''
# Water Level Trends for PA Groundwater 
'''

# Separate layout into two columns 1) map 2) trends plot
col1, col2 = st.columns(2)


### LOAD IN DATA ###
# Trends data
trends_all_sites, all_sites = load_dat()
trends_name, pa_wells_info = tidy_dat(trends_all_sites, all_sites)

# Initialize coordinates user will choose
latlong = 0,0




### CREATE INTERACTIVE MAP ###
# Put map in column 1
with col1:
    # Create interactive map
    m = fl.Map(location=[41.2033, -77.66], zoom_start=6.75)
    
    # Create a geopandas latlong frame so we can create interactive dots using geopandas
    gdf = getgeodf(pa_wells_info)
    
    # This function creates clickable dots
    gdf.explore(
        m = m,
        color = "red",
        marker_kwds=dict(radius=8, fill=True),
        tooltip="station_nm",
        tooltip_kwds=dict(labels=False),
        name="station_nm"
         )
    
    # This produces the map in streamlit. This HAS TO COME AFTER THE MAP IS FINISHED
    gw = st_folium(m, height=450, width=530)



### GET USER INPUT ###
# If the user clicks, pull lat long values of click
if gw.get("last_clicked"):
    # Store lat/long vals from user
    latlong = get_pos(gw["last_clicked"]["lat"], gw["last_clicked"]["lng"])

### PLOT TRENDS FIGURE ### 
# Put the trends plot in column 2
with col2:
    # See if lat long selection matches a site and then produce trends plot for that site
    if latlong is not None:
        option = choose_site(latlong, gdf)
        if option != 0:
            fig = plot_dat(trends_name, option)
            st.plotly_chart(fig)
        else: 
            '''
            Choose a USGS groundwater site to get started
            '''

    


    
    


    
    
    