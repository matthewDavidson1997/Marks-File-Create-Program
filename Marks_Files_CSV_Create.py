from os import system
from pathlib import Path
from random import randint
import re
from typing import Literal

import numpy as np
import pandas as pd


FILEPATH = Path('Z:\Personal\Marks File Create Program\Marks_Files')
POS_CODES = pd.read_csv('Z:\Personal\Marks File Create Program\POS_Codes.csv')

HEADER = ['Purchase Order Number', 'Item Number', 'Centre No', 'Centre No (SAP)', 'Candidate No',
          'Candidate No (SAP)', 'ATA Candidate Number', 'Programme of Study Code', 'Module Code', 'Module Booking GUID',
          'Assessment Event Date', 'Assessment Event Sitting', 'Module Question Paper Version', 'Candidate Status',
          'Measure Def Code', 'Measure Def Desc', 'Measure Def Level', 'Candidate Mark', 'Examiner Id (UCLES ID)', 'Delivery Method']


def get_pos() -> str:
    """Function to take and validate POS input

    Returns:
        str: Validated POS
    """
    while True:
        pos = input("Enter POS (in format D###): ").upper()
        if pos not in POS_CODES['Programme of Study Code'].unique():
            print("Invalid POS, please try again")
            continue
        return pos


def get_kad() -> str:
    """Function to take and validate KAD input

    Returns:
        str: Validated KAD
    """
    # Define expected input for kad. This would need updating in 2030
    patt = re.compile("^[0-3][\d][/][0-1][\d][/][2][0][1-2][\d]$")
    while True:
        kad = input("Enter KAD (in format DD/MM/YYYY): ")
        match = patt.match(kad)
        if not match:
            print("Invalid KAD, please try again")
            continue
        return kad


def get_sitting() -> str:
    """Function to take and validate sitting input

    Returns:
        str: Validated sitting
    """
    while True:
        sitting = input("Enter sitting (AM, PM, EV): ").upper()
        if sitting not in ["AM", "PM", "EV"]:
            print("Invalid sitting, please try again")
            continue
        return sitting


def get_centre() -> str:
    """Function to take and validate centre input

    Returns:
        str: validated centre
    """
    centre_patts = [re.compile("^[\d]{5}$"), re.compile("^[A-Z]{2}[\d]{3}$")]
    while True:
        centre = input("Enter centre number: ").upper()
        if not any([pat.match(centre) for pat in centre_patts]):
            print("Invalid centre, please try again")
            continue
        return centre


def get_candidates():
    patt = re.compile("^(?P<min_cand>[1-9][\d]*)[\s]+(?P<max_cand>[1-9][\d]*)$")
    while True:
        candidates = input("Enter the first and last candidate number (for example '1 10' for 10 candidates): ")
        candidates = candidates.strip()
        match = patt.match(candidates)
        if not match:
            print("Invalid candidate range, please try again")
            continue
        min_cand = int(match.groupdict()["min_cand"])
        max_cand = int(match.groupdict()["max_cand"])
        if max_cand < min_cand:
            print("Invalid candidate range, please try again")
            continue
        return range(min_cand, max_cand + 1)


def get_qpvs(candidates: range, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for module in df['Module Code'].unique():
        # Get user to enter mark for module
        qpv = input(f"Enter QPV for {module}: ")
        for cand in candidates:
            # Put entered mark into each row
            df.loc[(df['Module Code'] == module) & (df['Candidate No'] == cand), 'Module Question Paper Version'] = qpv
    return df


def add_details_to_df(df: pd.DataFrame, kad, sitting, centre) -> pd.DataFrame:
    df = df.copy()
    df['Assessment Event Date'] = kad
    df['Assessment Event Sitting'] = sitting
    df['Centre No'] = centre
    return df


def mark_scheme():
    option_patt = re.compile("^[1-4]$")
    while True:
        choice = input("Choose an option from the following list:\n\
            1: Use full marks for all candidates\n\
            2: Use random marks for all candidates\n\
            3: Use specific marks for each module but shared by candidates\n\
            4: Choose individual marks for each candidate and module\n")
        match = option_patt.match(choice)
        if not match:
            print("Invalid option entered, please try again")
            continue
        return int(choice)


def validate_mark(mark, max_mark):
    if mark <= max_mark and mark >= 0:
        return True


def assign_marks(df: pd.DataFrame, option: Literal[1, 2, 3, 4]) -> pd.DataFrame:
    """_summary_

    Args:
        df (pd.DataFrame): _description_
        option (Literal[1, 2, 3, 4]): _description_

    Returns:
        pd.DataFrame: _description_
    """
    df = df.copy()
    if option == 1:
        # Set candidate mark as the maximum mark
        df['Candidate Mark'] = df['Max_Mark']
    elif option == 2:
        # Enter a random mark for each row within range of max mark
        df['Candidate Mark'] = df['Max_Mark'].apply(lambda x: randint(0, x))
    elif option == 3:
        # Get each distinct module code
        for module in df['Module Code'].unique():
            # Get the maximum possible mark for that module
            max_mark = df[df['Module Code'] == module]['Max_Mark'].to_list()[0]
            # Get user to enter mark for module
            mark = input(f"Enter mark for {module} (max: {max_mark}): ")
            # Put entered mark into each row
            df.loc[df['Module Code'] == module, 'Candidate Mark'] = mark
    elif option == 4:
        # Create list to store marks for each candidate
        marks = []
        for idx, row in df.iterrows():
            # Get the maximum possible mark for that row
            max_mark = row['Max_Mark']
            #valid_mark = False
            #while not valid_mark:
                # Get mark from user input
            mark = int(input(f"Enter mark for {row['Module Code']} {row['Candidate No']} (max: {max_mark}): "))
                #valid_mark = validate_mark(mark, max_mark)
            # Add entered mark to list
            marks.append(int(mark))
        # Add marks from list to candidate marks column
        df['Candidate Mark'] = marks
    return df


def add_candidates_to_df(candidates: range, df: pd.DataFrame, candidate_df: pd.DataFrame) -> pd.DataFrame:
    # For each candidate in the range of candidates given add candidate number
    # to a new column in dataframe
    for cand in candidates:
        temp_df = df.copy()
        temp_df['Candidate No'] = cand
        # Concatenate the dataframe for each candidate
        candidate_df = pd.concat([candidate_df, temp_df], ignore_index=True)
    candidate_df['Max_Mark'] = candidate_df['Max_Mark'].astype(np.uint8)
    return candidate_df


def get_qpvs_for_candidates(pos_df):
    # create an empty dataframe to store data for all candidates
    candidate_df = pd.DataFrame(columns=HEADER)
    choice = "y"
    while choice == "y":
        candidates = get_candidates()
        candidate_df = add_candidates_to_df(candidates=candidates, df=pos_df, candidate_df=candidate_df)
        # Take QPV from user and add to dataframe
        candidate_df = get_qpvs(candidates, candidate_df)
        choice = input("Would you like to add another candidate range? y/n:")
    # Ask how the user would like to add marks
    marking_choice = mark_scheme()
    # Add marks to each candidate
    candidate_df = assign_marks(candidate_df, marking_choice)
    return candidate_df


def save_df_to_csv(df: pd.DataFrame):
    # Drop Max Marks column for output csv
    df = df.drop(columns=['Max_Mark'])
    kad, pos, centre, sitting = df['Assessment Event Date'].unique(), df['Programme of Study Code'].unique(),\
        df['Centre No'].unique(), df['Assessment Event Sitting'].unique()
    
    kad, pos, centre, sitting = str(kad[0]), pos[0], centre[0], sitting[0]

    df['Candidate No'] = df['Candidate No'].apply(lambda x: f"{x:>04}")
    # Remove invalid filepath symbols
    file_kad = kad.replace("/", "")
    # Save df to CSV with filename using session details
    df.to_csv(str(FILEPATH) + f'\marksfile_{pos}_{centre}_{file_kad}{sitting}.csv', index=False)


def input_choice():
    return input("How would you like to enter data? \n\
        1. Enter in format (POS) (KAD) (Sitting) (Centre)\n\
        2. Enter separately\n")


def main():
    choice = "y"
    while choice == "y":
        system('cls')
        print("Marks file creation program")
        # Take session details from user
        pos = get_pos()
        kad = get_kad()
        sitting = get_sitting()
        centre = get_centre()
        # Slice df and add the provided details
        pos_df = POS_CODES[POS_CODES['Programme of Study Code'] == pos].copy()
        pos_df = add_details_to_df(pos_df, kad, sitting, centre)
        candidate_df = get_qpvs_for_candidates(pos_df=pos_df)
        save_df_to_csv(candidate_df)
        choice = input("Generate another marks file? y/n:")


if __name__ == "__main__":
    main()
