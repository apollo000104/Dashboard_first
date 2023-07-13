import pandas as pd

df = pd.read_csv('/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/new/to_full1.csv', index_col='Unnamed: 0')

df = df.fillna('NULL')

df.to_csv('to_db.csv', index=False)