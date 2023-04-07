import pandas as pd
import numpy as np


def get_poly_depreciation(coeff, ownership_term, miles_driven):
    # create an array incremental array of 1000
    miles = np.arange(1000, 40000, 1000)
    y_hat = []

    # add the estimated vehicle value per 1k miles to the array
    for m in miles:
        yhat = coeff[1]*np.log10([m]) + coeff[0]
        #print('A Porsche Carrera S with', m, 'miles will cost: $', "{:,}".format(round(y_hat[0], 0)))
        y_hat.append(yhat)

    # flatten the arrays
    y_hat = [num for sublist in y_hat for num in sublist]
    y_hat = ['${:0,.0f}'.format(x) for x in y_hat]

    df_depr = pd.DataFrame({"Miles": miles.flatten(), "Est Price": y_hat})
    #df_depr['Trim'] = 'S'

    # use the diff() fn to get the per 1k miles depreciation
    df_depr['Est Price Float'] = df_depr['Est Price'].replace('[\$,]', '', regex=True).astype(float)
    df_depr['Est Price Depr'] = df_depr['Est Price Float'].diff()
    
    # use the inputs provided by user to get total miles
    total_ownership_miles = ownership_term * miles_driven
    # convert the total_ownership_miles to a factor of 1000 so you can use it as a positional index since the df is 1 row per every 1000 miles
    total_ownership_miles = int(((ownership_term * miles_driven) / 1000) - 1)

    # use the total_ownership_miles as positional index to get depreciation at beginning of the curve
    # vs at the end of the curve
    first_term_miles = df_depr.iloc[0:total_ownership_miles, :]['Est Price Depr'].sum()
    third_term_miles = df_depr.iloc[29:(29+total_ownership_miles), :]['Est Price Depr'].sum()
    
    return first_term_miles, third_term_miles
    