from pathlib import Path
import pandas as pd
import glob
import openpyxl


PATH = str(Path.cwd())
Path(PATH + '\Marks Files\Marks Scenarios').mkdir(parents=True, exist_ok=True)
FOLDERPATH = (PATH + '\Marks Files\Marks Scenarios')
FILES = glob.glob(FOLDERPATH + '\*.xlsx')


def get_sheets(file):
    wb = openpyxl.load_workbook(file, data_only=True)
    sheets = []
    for sheet in wb.sheetnames:
        if sheet != 'Notes':
            sheets.append(sheet)
    return sheets


def delete_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_to_drop = []
    cols_to_keep = ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'MAX', 'MINA', 'MAXB',
                    'MINB', 'MAXC', 'MINC', 'MAXB2', 'MINB2', 'COMPNR', 'ALLNR']
    for cols in df:
        if cols not in cols_to_keep:
            cols_to_drop.append(df.columns.get_loc(cols))
    df = df.drop(df.columns[cols_to_drop], axis=1)
    df.rename(columns={'Unnamed: 0': 'Long Measure Def', 'Unnamed: 1': 'Measure Def', 'Unnamed: 2': 'Max_Mark'}, inplace=True)
    return df


def delete_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows_to_delete = []
    for idx, row in df.iterrows():
        if pd.isna(df.iloc[idx, 0]) and idx > 1:
            rows_to_delete.append(idx)
    df = df.drop(index=rows_to_delete)
    return df


def main():
    files = FILES
    for file in files:
        try:
            sheets = get_sheets(file)
            print(sheets)
            new_filename = file.replace('Z:\Personal\Marks File Create Program\Marks_Files\Marks_Scenarios\\', '')
            new_filename = new_filename.replace('.xlsx', '.csv')
            print(new_filename)
            for sheet in sheets:
                df = pd.read_excel(file, sheet_name=sheet)
                df = delete_columns(df)
                df = delete_rows(df)
                print(df)
                df.to_csv(str(FOLDERPATH) + f'\\new {sheet} {new_filename}', index=False)
        except TypeError:
            print("TypeError")


if __name__ == "__main__":
    main()
