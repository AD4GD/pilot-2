import numpy as np
import pandas as pd

s=pd.Series ([0,1,2,3,np.nan,8])
dates=pd.date_range ("20230101",periods = 10)
df=pd.DataFrame(np.random.randn(10, 4),index=dates,columns=list("FGHJ"))
df2=pd.DataFrame(
    { 
        "num": pd.RangeIndex(start=1,stop=len(dates)),
        "date": dates,
    }
)
df2.to_csv ("test_1.csv")
