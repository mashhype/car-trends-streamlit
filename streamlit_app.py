# streamlit_app.py

import pandas as pd
import numpy as np
import snowflake.connector
import streamlit as st
import ipywidgets
print(ipywidgets.__version__)
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
from PIL import Image
import car_functions as cf

st.set_page_config(layout="centered")

# Initialize connection.
# Uses st.experimental_singleton to only run once.
## @st.cache_resource
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"])

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.cache_data(persist="disk")
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetch_pandas_all()

df = run_query("SELECT VIN, YEAR, MODEL, TRIM, TRANSMISSION, MAX(SCRAPED_AT_DATE) SCRAPED_AT_DATE, MAX(MILES) MILES, AVG(PRICE) PRICE FROM PORSCHE_911 WHERE SCRAPED_AT_DATE BETWEEN DATEADD(year, -1, GETDATE()) AND GETDATE() GROUP BY VIN, YEAR, MODEL, TRIM, TRANSMISSION ORDER BY SCRAPED_AT_DATE;")


## consolidate trim labels
df['TRIM'] = np.where(df['TRIM'] == 'S', 'Carrera S', np.where(df['TRIM'].isin(['Base', 'CARRERA']), 'Carrera', np.where(df['TRIM'] == 'GTS', 'Carrera GTS', df['TRIM'])))


fig = go.FigureWidget()
fig = px.bar(x=df.TRIM.value_counts().index.tolist(), 
             y=df.TRIM.value_counts(normalize=True).tolist(), 
             width=1400, height=800)

fig.layout.title = '% of Listings By Trim Level for Porsche 911 (2012 - 2022)'
fig.layout.yaxis.tickformat = ',.0%'

st.title('Welcome To CarTrends.ai')

image = Image.open('Porsche_By_Generation_resized.jpg')
st.image(image, caption='911 By Generation')

st.subheader('Tell us what trim you are interested and we will share some insights with you..')

st.markdown('Select a year:')
options_yr = st.selectbox('', [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019])

st.markdown('Select a trim:')
options_trim = st.selectbox('', ['Carrera', 'Carrera S', 'Carrera GTS', 'Turbo', 'Turbo S', 'GT3'])

st.write('You selected:')
# s = ''
# for i in options:
#     s += "- " + i + "\n"

st.markdown(str(options_yr) + " " + options_trim)
st.markdown('##')

st.markdown('How many years do you plan to own the car:')
ownership_term = st.slider('', 1, 10, 3)
st.markdown('##')
#ownership_term_string = "You plan to own the car for " + str(ownership_term) + " years."
#st.markdown(ownership_term_string)
st.markdown('##')

st.markdown("Now tell us how many miles will you drive the car per year:")
miles_driven = st.slider('', 2000, 25000, 3000, step=1000)
#st.markdown(miles_driven_string)
st.markdown('##')

## Scatterplot with Trendline (Polynomial regression)
df_temp = df[(df.TRIM == options_trim) & 
                 (df.MILES.between(1, 100000)) & 
                 (df.YEAR == options_yr)][['TRIM', 'MILES', 'PRICE']]

st.markdown('##')
min_year = df.SCRAPED_AT_DATE.min()
max_year = df.SCRAPED_AT_DATE.max()

st.markdown('In the scatterplot below, each dot represents a car that was listed by a US dealer between ' + str(min_year) + ' and ' + str(max_year) + ' . There are a total of ' + str(df_temp.TRIM.count()) + ' samples in the plot below. The trend line (i.e. line of best fit) gives us an idea of the relationship between **PRICE** and **MILES** for the different trim levels shown.')
st.markdown('##')
st.markdown('##')

fig = px.scatter(df_temp, 
                 x="MILES", 
                 y="PRICE", 
                 color="TRIM", 
                 template='plotly', 
                 width=600, height=400, 
                 trendline="ols", 
                 trendline_options=dict(log_x=True))

fig.layout.title = 'Scatterplot With Trendline By Trim Level for a ' + str(options_yr) + ' Porsche 911'
# Plot!
st.plotly_chart(fig, use_container_width=True)


### Apply the polynomial regression to show cost per $1k miles:
results = px.get_trendline_results(fig)
coeff = results.query(f"TRIM == '{options_trim}'").px_fit_results.iloc[0].params

## get the first third and third 10k miles depreciation cost
first, third = cf.get_poly_depreciation(coeff, ownership_term, miles_driven)

first = int(first)
third = int(third)

st.write(f'Assuming you drive the car for a **total of {ownership_term * miles_driven} miles**, a 991 generation **{str(options_yr) } {options_trim}** will depreciate an average of **{first}** dollars if purchased with 1K miles, while it will only lose an average of **{third}** dollars if purchased around 30k miles.')

# Another scatter plot but with bubbles
# df_temp = df_grp.groupby(['YEAR', 'TRIM_CLEAN']).agg({'VIN': 'count', 
#                                                 'MILES':'mean',
#                                                 'PRICE':'mean'}).reset_index()
