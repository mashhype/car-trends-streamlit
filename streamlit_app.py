# streamlit_app.py
import logging
import pandas as pd
import numpy as np
import snowflake.connector
import streamlit as st
import statsmodels
import ipywidgets
#print(ipywidgets.__version__)
import plotly.graph_objects as go
#import matplotlib.pyplot as plt
import plotly.express as px
from PIL import Image
import car_functions as cf

logger = logging.getLogger(__name__)

st.set_page_config(layout="centered")

# # Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"], client_session_keep_alive=True)

logger.info("Starting logging...")
conn = init_connection()




# # Perform query.
# # Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetch_pandas_all()


logger.info("About to run query...")
df = run_query("select * from porsche_911 limit 100;")
logger.info("Query has been run...")


## read in csv dataset
# df = pd.read_csv('porsche_911_sample.csv')


## summarize data and remove duplicates
df_grp = df.groupby(['VIN', 'YEAR', 'MODEL', 'TRIM', 'TRANSMISSION']).agg({'SCRAPED_AT_DATE':'max',
                                                                           'MILES':'max',
                                                                           'PRICE':'mean'}).reset_index().sort_values('VIN')


# with st.form("my_form"):
#    st.write("Inside the form")
#    slider_val = st.slider("Form slider")
#    checkbox_val = st.checkbox("Form checkbox")

#    # Every form must have a submit button.
#    submitted = st.form_submit_button("Submit")
#    if submitted:
#        st.write("slider", slider_val, "checkbox", checkbox_val)

# st.write("Outside the form")


## consolidate trim labels
df_grp['TRIM_CLEAN'] = np.where(df_grp['TRIM'] == 'S', 'Carrera S',
                       np.where(df_grp['TRIM'].isin(['Base', 'CARRERA']), 'Carrera',
                       np.where(df_grp['TRIM'] == 'GTS', 'Carrera GTS', df_grp['TRIM'])))


fig = go.FigureWidget()
fig = px.bar(x=df_grp.TRIM_CLEAN.value_counts().index.tolist(), 
             y=df_grp.TRIM_CLEAN.value_counts(normalize=True).tolist(), 
             width=1400, height=800)

fig.layout.title = '% of Listings By Trim Level for Porsche 911 (2012 - 2022)'
fig.layout.yaxis.tickformat = ',.0%'


st.title('Welcome To CarTrends.ai')

image = Image.open('Porsche_By_Generation_resized.jpg')
st.image(image, caption='911 By Generation')

st.subheader('Tell us what trim you are interested and we will share some insights with you..')

st.markdown('Select a trim:')
options = st.selectbox('', ['Carrera', 'Carrera S', 'Carrera GTS', 'Turbo', 'Turbo S', 'GT3'])

st.write('You selected:')
# s = ''
# for i in options:
#     s += "- " + i + "\n"

st.markdown(options)
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
df_temp = df_grp[(df_grp.TRIM_CLEAN == options) & 
                 (df_grp.MILES.between(1, 100000)) & 
                 (df_grp.YEAR.between(2012, 2019))][['TRIM_CLEAN', 'MILES', 'PRICE']] #.sample(frac=.08)

st.markdown('##')
st.markdown('In the scatterplot below, each dot represents a car that was listed by a US dealer between [] and []. The trend line (i.e. line of best fit) gives us an idea of the relationship between **PRICE** and **MILES** for the different trim levels shown.')


fig = px.scatter(df_temp, 
                 x="MILES", 
                 y="PRICE", 
                 color="TRIM_CLEAN", 
                 template='plotly', 
                 width=1000, height=800, 
                 trendline="ols", 
                 trendline_options=dict(log_x=True))

fig.layout.title = 'Scatterplot With Trendline By Trim Level for Porsche 911'
# Plot!
st.plotly_chart(fig, use_container_width=False)


### Apply the polynomial regression to show cost per $1k miles:
results = px.get_trendline_results(fig)
coeff = results.query(f"TRIM_CLEAN == '{options}'").px_fit_results.iloc[0].params

## get the first third and third 10k miles depreciation cost
first, third = cf.get_poly_depreciation(coeff, ownership_term, miles_driven)

first = int(first)
third = int(third)

# st.write(ownership_term)
# st.write(miles_driven)
# st.write(total_ownership_miles)

st.write(f'Assuming you drive the car for a **total of {ownership_term * miles_driven} miles**, a 991 generation (2012 - 2019) **{options}** will depreciate an average of **{first}** dollars if purchased with 1K miles, while it will only lose an average of **{third}** dollars if purchased around 30k miles.')

# Another scatter plot but with bubbles
# df_temp = df_grp.groupby(['YEAR', 'TRIM_CLEAN']).agg({'VIN': 'count', 
#                                                 'MILES':'mean',
#                                                 'PRICE':'mean'}).reset_index()
