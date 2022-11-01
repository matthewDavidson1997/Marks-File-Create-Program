from pathlib import Path

import pandas as pd

FILEPATH = Path('Z:\Personal\Marks File Create Program\Marks_Files\Marks_Scenarios')

df = pd.read_excel(str(FILEPATH) + '\Advanced D435 PB Rebranding QA1 2022 marks scenarios .xlsx', sheet_name=1)

for cols in df:
    print(cols)
    cols_to_drop = []
    if cols not in ['Unnamed: 0', 
                    'Unnamed: 1', 
                    'Unnamed: 2', 
                    'MAX', 
                    'MINA', 
                    'MAXB', 
                    'MINB', 
                    'MAXC', 
                    'MINC', 
                    'MAXB2', 
                    'MINB2', 
                    'COMPNR', 
                    'ALLNR']:
        df.drop(df[cols])
    print(cols)
