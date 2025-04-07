import pandas as pd

CSV1 = 'Cat1.csv'
CSV2 = 'Cat2.csv'

OUT  = 'Prod_Cat.csv'

df1 = pd.read_csv(CSV1)
df2 = pd.read_csv(CSV2)
combined = pd.concat([df1, df2], ignore_index=True)
combined.to_csv(OUT, index=False)