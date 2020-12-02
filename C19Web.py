#!/usr/bin/env python3

#
# C19Web.py
#
# C19Web is a web application written in Python and using
# Streamlit as the presentation method and Streamlit Share
# make it generally available.
#
# The structure of this program has all the Streamlit code 
# in the main program because of Streamlit requirements.
#

import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st
import urllib

from streamlit.elements.doc_string import CONFUSING_STREAMLIT_MODULES

st.set_page_config(
    page_title="B.C. Covid-19",
    page_icon="😷",
    layout="centered",
    initial_sidebar_state="auto",
)

# 'country', 'province', 'lastDate'     
# 'latitude', 'longitude'    
# 'dates'        
# 'confirmed', 'confirmedNew', 'confirmedNewMean'
# 'deaths', 'deathsNew', 'deathsNewMean'
index_url_csv  = 'https://jpaulhart.github.io/Index.csv'
index_url_json = 'https://jpaulhart.github.io/Index.json'

# "Date", "Region", "New_Tests", "Total_Tests", "Positivity", "Turn_Around"
bc_tests_url = 'http://www.bccdc.ca/Health-Info-Site/Documents/BCCDC_COVID19_Dashboard_Lab_Information.csv'
# "Reported_Date","HA","Sex","Age_Group","Classification_Reported"
bc_cases_url = 'http://www.bccdc.ca/Health-Info-Site/Documents/BCCDC_COVID19_Dashboard_Case_Details.csv'

# province, lastDate, latitude, longitude,
# date[], confirmed[], confirmedNew[], confirmedNewMean[], deaths[], deathsNew[], deathsNewMean[]            
base_url = 'https://jpaulhart.github.io'

#-------------------------------------------------------------------------
# Contains a collection or group of countries in one plot 
#-------------------------------------------------------------------------

class Countries():
    def __init__(self, groupName, countryList = []):
        self.groupName = groupName
        self.countryList = countryList
    
#-------------------------------------------------------------------------
# Country class contains all the input data required to produce a plot
#-------------------------------------------------------------------------

class Country():
  def __init__(self, name):
    self.name = name

# #######################################################################################
# Read data and cache
# #######################################################################################

#@st.cache
def read_csv(url):
    fixed_url = url.replace(' ', '%20')
    return pd.read_csv(fixed_url)

# #######################################################################################
# Setup global data
# #######################################################################################

dfIndex = read_csv(index_url_csv)
allCountries = dfIndex['Country'].tolist()
countries = []

provinces = ('British Columbia',
             'Alberta',
             'Saskatchewan',
             'Manitoba',
             'Ontario',
             'Quebec',
             'Newfoundland and Labrador',
             'New Brunswick',
             'Nova Scotia'
             'Prince Edward Island'
            )
selected_provinces = ('British Columbia') 

time_frames = ('All', '1 Week', '2 Weeks', '3 Weeks', '1 Month', '3 Months', '6 Months')
time_frame = 'All'

last_date = ''
dfLast = read_csv(urllib.parse.urljoin(base_url, 'Canada.csv'))
dfLast = dfLast.tail(n=1)
last_date = dfLast['Date'].values[0]

world_pop = read_csv(urllib.parse.urljoin(base_url, 'WorldPop.csv'))

# Provincial Population
prov_pop = {
    'BC' : 5.071,
    'AL' : 4.371,
    'SA' : 1.174,
    'MB' : 1.369,
    'ON' : 14.57,
    'PQ' : 8.485,
    'NL' : 0.552,
    'NB' : 0.777,
    'NS' : 0.971,
    'PE' : 0.156,
}

# #######################################################################################
# Select days based time_frame
# #######################################################################################

def df_days(dfProv, last_date, time_frame):

    first_date = parser.parse('2020-03-01')
    in_date = parser.parse(last_date)

    if time_frame == time_frames[1]:
        date_after = in_date - relativedelta(weeks=1)
    elif time_frame == time_frames[2]:
        date_after = in_date - relativedelta(weeks=2)
    elif time_frame == time_frames[3]:
        date_after = in_date - relativedelta(weeks=3)
    elif time_frame == time_frames[4]:
        date_after = in_date - relativedelta(months=1)
    elif time_frame == time_frames[5]:
        date_after = in_date - relativedelta(months=3)
    elif time_frame == time_frames[6]:
        date_after = in_date - relativedelta(months=6)
    elif time_frame == time_frames[0]:
        date_after = first_date
    else:
        date_after = first_date

    out_date = date_after.strftime("%Y-%m-%d")
    dfOut = dfProv[dfProv['Date'] >= out_date]
    return dfOut

# #######################################################################################
# Setup page
# #######################################################################################

def stSetup():
    global selected_provinces
    global time_frame
    global last_date
    global countries

    st.header('Covid-19 Tracker')
    st.markdown(f'###### Report Date: {last_date}')
    st.markdown(f'###### Reporting time frame: {time_frame}')
    st.markdown('## ')

    # Setup sidebar
    st.sidebar.markdown('## Options')
    st.sidebar.markdown('### Select Time Frame')
    time_frame = st.sidebar.selectbox('Select analysis time period:', time_frames)

    st.sidebar.markdown('### Select Countries')
    countries = st.sidebar.multiselect('Select countries:', 
                                        allCountries,
                                        ['Canada', 'Italy', 'Spain', 'Portugal', 'Thailand', 'Uruguay']
                                      )

    st.sidebar.markdown('----')
    st.sidebar.markdown('### About')
    st.sidebar.markdown('The majority of the data used in this application is sourced from the [Johns Hopkins University Center for Systems Science and Engineering (JHU CCSE)](https://data.humdata.org/dataset/novel-coronavirus-2019-ncov-cases).')    
    st.sidebar.markdown('The testing data for British Columbia is from the [BC Centre for Disease Control](http://www.bccdc.ca/Health-Info-Site/Documents/BCCDC_COVID19_Dashboard_Lab_Information.csv)')
    return

# #######################################################################################
# Section 1
#     C19BCTable - Table with number of tests, %age of those positive, turn around time
#     Graph of a) confirmed new b) deaths new
#     Graph of province compare
#     Province Summary:
#      - new cases, deaths last 7 days
#      - new tests, positivity last 7 days
#      - Graphs
#      - Sidebar select provinces
# #######################################################################################

def stSection1():
    global last_date

    prov = 'British Columbia'
    
    file_name = f'{prov}.csv'.replace(' ', '%20')
    dfProv = pd.read_csv(urllib.parse.urljoin(base_url, file_name))
    
    dfTests = read_csv(bc_tests_url)
    dfTable = dfTests.copy() 
    dfTable['New_Positives'] = dfTable['New_Tests'] * (dfTable['Positivity'] / 100)

    dfTable = dfTable.groupby('Date').agg({'New_Tests': 'sum', 'New_Positives': 'sum', 'Positivity': 'mean', 'Turn_Around': 'mean'})
    dfTable = dfTable.sort_values('Date', ascending=False)
    dfTable = pd.merge(dfProv, dfTable, on=['Date'])
    print(dfTable.tail(n=10))
    #dfLast = dfProv.tail(n=1)
    #last_date = dfLast['Date'].values[0]
    dfProv = df_days(dfProv, last_date, time_frame)
    dfProv = dfProv.sort_values(by=['Date'], ascending=True)
    #st.markdown('----')
    st.markdown(f'#### {prov}')
    #st.markdown(f'###### Report Date: {last_date}')

    col1, col2 = st.beta_columns(2)
    #with col1:
    stProvTable(dfTable)
    st.markdown('## ')
    #with col2:
    stProvGraphs(dfProv)

#-----------------------------------------------------------------------------
# Provincial Stats Graph for specified time span
#-----------------------------------------------------------------------------

def stProvGraphs(dfProv):

    #-------------------------------------------------------------------------
    # Create Confirmed New Plot
    #-------------------------------------------------------------------------
    col1, col2 = st.beta_columns(2)
    with col1:

        #st.markdown(f'##### New Cases')

        fig1 = plt.figure(1, figsize=(8, 5))

        plt.title('New Cases - Smoothed', fontsize='large')
        plt.xlabel="Date"
        plt.ylabel="Number"

        #plt.xticks(rotation=45)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(100))

        plt.plot(dfProv['Date'], dfProv['ConfirmedNewMean'], label='New Cases - Smoothed')
        plt.grid(b=True, which='major')
        st.pyplot(fig1)
        plt.close()

    #-------------------------------------------------------------------------
    # Create Deaths New Plot
    #-------------------------------------------------------------------------

    with col2:
        #st.markdown(f'##### New Deaths')
        
        fig2 = plt.figure(2, figsize=(8, 5))

        plt.title('New Deaths - Smoothed')
        plt.xlabel="Date"
        plt.ylabel="Number"

        #plt.xticks(rotation=45)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(100))

        plt.plot(dfProv['Date'], dfProv['DeathsNewMean'], label='New Deaths - Smoothed')
        plt.grid(b=True, which='major')
        st.pyplot(fig2)
        plt.close()
        #if prov == 'British Columbia':
        #stBCCases(dfProv)

#-----------------------------------------------------------------------------
# Provincial Stats Table
#-----------------------------------------------------------------------------

def stProvTable(dfProv):
    
        #st.markdown(f'##### 10 Days')

        # Table of details for last week 
        cases_data = '<div style="font-size: small">\n'
        cases_data += '<table border=1>\n'
        cases_data += '<tr><th> </th><th colspan=2 style="text-align:center">Cases</th><th colspan=2 style="text-align:center">Deaths</th><th colspan=4 style="text-align:center">Testing</th></tr>\n'
        cases_data += '<tr><th>Date</th><th>Total</th><th>New</th><th>Total</th><th>New</th><th>New</th><th>Positives</th><th>% Pos.</th><th>Hours</th></tr>\n'
        #cases_data += '| :----- | ----------: | --------: | -----------: | ---------: |\n'
        row_count = 0
        dfSorted = dfProv.sort_values(['Date'], ascending=False)
        for index, row in dfSorted.iterrows():
            date = row['Date'] 
            confirmed = row['Confirmed']
            confirmed = "{:,}".format(confirmed)
            confirmedNew = row['ConfirmedNew']
            confirmedNew = "{:,}".format(confirmedNew)
            deaths = row['Deaths']
            deaths = "{:,}".format(deaths)
            deathsNew = row['DeathsNew']
            deathsNew = "{:,}".format(deathsNew)
            #New_Tests  New_Positives  Positivity  Turn_Around
            newTests = row['New_Tests']
            newTests = "{:,.0f}".format(newTests)
            newPositives = row['New_Positives']
            newPositives = "{:,.0f}".format(newPositives)
            positivity = row['Positivity']
            positivity = "{:.1f}".format(positivity)
            turnAround = row['Turn_Around']
            turnAround = "{:.1f}".format(turnAround)
            cases_data += f'<tr>'
            cases_data += f'<td nowrap>{date}</td><td style="text-align:right">{confirmed}</td>'
            cases_data += f'<td style="text-align:right">{confirmedNew}</td>'
            cases_data += f'<td style="text-align:right">{deaths}</td>'
            cases_data += f'<td style="text-align:right">{deathsNew}</td>'
            cases_data += f'<td style="text-align:right">{newTests}</td>'
            cases_data += f'<td style="text-align:right">{newPositives}</td>'
            cases_data += f'<td style="text-align:right">{positivity}%</td>'
            cases_data += f'<td style="text-align:right">{turnAround} hours</td>'
            cases_data += f'</tr>' + '\n'
            row_count += 1
            if row_count >= 10:
                cases_data += '</table>\n'
                cases_data += '</div>\n'
                break
        st.markdown(cases_data, unsafe_allow_html=True)

#-----------------------------------------------------------------------------
# Provincial Stats Table
#-----------------------------------------------------------------------------

def stBCCases(dfProv):
    # "Reported_Date","HA","Sex","Age_Group","Classification_Reported"
    case_Url = 'http://www.bccdc.ca/Health-Info-Site/Documents/BCCDC_COVID19_Dashboard_Case_Details.csv'
    dfCase = read_csv(case_Url) 
    dfCase = df_days(dfCase, last_date, time_frame)
    dfCase['Year_Month'] = dfCase['Reported_Date'].map(lambda reported_date: reported_date[0:7])
    dfCase = dfCase.sort_values(by=['Reported_Date', 'HA'])

    dfCrosstab = pd.crosstab(index=dfCase['Reported_Date'], columns=dfCase['HA'])
    dfCrosstab.plot(kind='barh')
    reportTitle = 'BC Lab Diagnosed Cases by Health Authority'
    plt.title(reportTitle, fontsize=10)
    fig3 = plt.figure(3, figsize=(15, 6))
    st.pyplot(fig3)

# #######################################################################################
# Section 2
#     Provincial compare
# #######################################################################################

def stSection2():
    global last_date

    st.markdown('----')
    st.markdown(f"#### Compare Canada's Largest Provinces")
    #st.markdown(f'###### Report Date: {last_date}')
    dfal = read_csv(urllib.parse.urljoin(base_url, 'Alberta.csv'))
    dfal = df_days(dfal, last_date, time_frame)
    dfal['ConfirmedNewPer1M'] = dfal['ConfirmedNewMean'] / prov_pop['AL']
    dfal['DeathsNewPer1M']    = dfal['DeathsNewMean'] / prov_pop['AL']
    dfbc = read_csv(urllib.parse.urljoin(base_url, 'British%20Columbia.csv'))
    dfbc = df_days(dfbc, last_date, time_frame)
    dfbc['ConfirmedNewPer1M'] = dfbc['ConfirmedNewMean'] / prov_pop['AL']
    dfbc['DeathsNewPer1M']    = dfbc['DeathsNewMean'] / prov_pop['AL']
    dfon = read_csv(urllib.parse.urljoin(base_url, 'Ontario.csv'))
    dfon = df_days(dfon, last_date, time_frame)
    dfon['ConfirmedNewPer1M'] = dfon['ConfirmedNewMean'] / prov_pop['AL']
    dfon['DeathsNewPer1M']    = dfon['DeathsNewMean'] / prov_pop['AL']
    dfqu = read_csv(urllib.parse.urljoin(base_url, 'Quebec.csv'))
    dfqu = df_days(dfqu, last_date, time_frame)
    dfqu['ConfirmedNewPer1M'] = dfqu['ConfirmedNewMean'] / prov_pop['AL']
    dfqu['DeathsNewPer1M']    = dfqu['DeathsNewMean'] / prov_pop['AL']
    #print(dfal.info())

    col1, col2 = st.beta_columns(2)

    #-------------------------------------------------------------------------
    # Create Confirmed New Plot
    #-------------------------------------------------------------------------

    with col1:

        #st.markdown(f'##### New Cases')

        fig1 = plt.figure(1, figsize=(8, 5))

        plt.title('Confirmed New Cases per Million', fontsize='large')
        plt.xlabel="Date"
        plt.ylabel="Number"

        #plt.xticks(rotation=45)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(75))

        #plt.plot(dfPr['date'], dfProv['confirmedNewMean'], label='New Cases - Smoothed')
        plt.plot(dfal['Date'], dfal['ConfirmedNewPer1M'], label='Alberta')
        plt.plot(dfbc['Date'], dfbc['ConfirmedNewPer1M'], label='British Columbia')
        plt.plot(dfon['Date'], dfon['ConfirmedNewPer1M'], label='Ontario')
        plt.plot(dfqu['Date'], dfqu['ConfirmedNewPer1M'], label='Quebec')

        # Add a legend
        plt.legend(['Alberta', 'British Columbia', 'Ontario', 'Quebec'])
        plt.grid(b=True, which='major')
        st.pyplot(fig1)
        plt.close()

    #-------------------------------------------------------------------------
    # Create Deaths New Plot
    #-------------------------------------------------------------------------

    with col2:

        #st.markdown(f'##### New Deaths')

        fig1 = plt.figure(1, figsize=(8, 5))

        plt.title('New Deaths per Million', fontsize='large')
        plt.xlabel="Date"
        plt.ylabel="Number"

        #plt.xticks(rotation=45)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(75))

        #plt.plot(dfPr['date'], dfProv['confirmedNewMean'], label='New Cases - Smoothed')
        plt.plot(dfal['Date'], dfal['DeathsNewPer1M'], label='Alberta')
        plt.plot(dfbc['Date'], dfbc['DeathsNewPer1M'], label='British Columbia')
        plt.plot(dfon['Date'], dfon['DeathsNewPer1M'], label='Ontario')
        plt.plot(dfqu['Date'], dfqu['DeathsNewPer1M'], label='Quebec')

        # Add a legend
        plt.legend(['Alberta', 'British Columbia', 'Ontario', 'Quebec'])
        plt.grid(b=True, which='major')
        st.pyplot(fig1)
        plt.close()

# #######################################################################################
# Section 3
#     Other countries
# #######################################################################################

def stSection3():
    global last_date

    st.markdown('----')
    st.markdown(f'#### Countries')

    col1, col2 = st.beta_columns(2)

    with col1:

        fig1 = plt.figure(1, figsize=(8, 5))

        plt.title('New Confirmed Cases', fontsize='large')
        plt.xlabel="Date"
        plt.ylabel="Number"

        #plt.xticks(rotation=45)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(75))

        for cty in countries:
            dfCountry = dfIndex[dfIndex['Country'] == cty]
            file_name = dfCountry['File'].values[0]
            file_url = urllib.parse.urljoin(base_url, file_name)
            df = read_csv(file_url)
            plt.plot(df['Date'], df['ConfirmedNewMean'], label=df['Country'])

        # Add a legend
        plt.legend(countries)
        plt.grid(b=True, which='major')
        st.pyplot(fig1)
        plt.close()

    with col2:
        fig1 = plt.figure(1, figsize=(8, 5))

        plt.title('New Deaths', fontsize='large')
        plt.xlabel="Date"
        plt.ylabel="Number"

        #plt.xticks(rotation=45)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(75))

        for cty in countries:
            dfCountry = dfIndex[dfIndex['Country'] == cty]
            file_name = dfCountry['File'].values[0]
            file_url = urllib.parse.urljoin(base_url, file_name)
            df = read_csv(file_url)
            plt.plot(df['Date'], df['DeathsNewMean'], label=df['Country'])

        # Add a legend
        plt.legend(countries)
        plt.grid(b=True, which='major')
        st.pyplot(fig1)
        plt.close()

#-------------------------------------------------------------------------
# Get dataframe for a country
#-------------------------------------------------------------------------

def getDfForCountry(countryName):
    global last_date

    country = countryName.replace(' ', '%20')
    df = read_csv(urllib.parse.urljoin(base_url, f'{country}.csv'))
    df = df_days(df, last_date, time_frame)

    return df

# ############################################################################
# Entry Point
# ############################################################################

stSetup()
stSection1()
stSection2()
stSection3()



