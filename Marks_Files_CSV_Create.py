"""Functionality to automate marking CSV file generation."""


import os
import re
from datetime import datetime
from pathlib import Path
from random import randint

import numpy as np
import pandas as pd


MARKSFOLDER = Path('Marks Files')
MARKSFOLDER.mkdir(parents=True, exist_ok=True)
POS_CODES = pd.read_csv('POS_Codes.csv')

HEADER = [
    'Purchase Order Number',
    'Item Number',
    'Centre No',
    'Centre No (SAP)',
    'Candidate No',
    'Candidate No (SAP)',
    'ATA Candidate Number',
    'Programme of Study Code',
    'Module Code',
    'Module Booking GUID',
    'Assessment Event Date',
    'Assessment Event Sitting',
    'Module Question Paper Version',
    'Candidate Status',
    'Measure Def Code',
    'Measure Def Desc',
    'Measure Def Level',
    'Candidate Mark',
    'Examiner Id (UCLES ID)',
    'Delivery Method'
]

REGEX_PATTERNS = {
    "Centre":
        re.compile(r"^([\d]{5}|[A-Z]{2}[\d]{3})$"),
    "QPV":
        re.compile(r"^[\d]*$"),
    "Mark Scheme":
        re.compile(r"^[1-4]$"),
    "Candidates":
        re.compile(r"^(?P<min_cand>[1-9][\d]*)[\s]+(?P<max_cand>[1-9][\d]*)$")
    }

# A dictionary of (prompt, repeat) pairs, keyed by function name
MESSAGE_DICT = {
    "POS": (
        "Enter POS (in format D###): ",
        "Invalid POS, please try again"
    ),
    "KAD": (
        "Enter KAD (in format DD/MM/YYYY): ",
        "Invalid date given, try again"
    ),
    "Sitting": (
        "Enter sitting (AM, PM, EV): ",
        "Invalid sitting, please try again"
    ),
    "Centre": (
        "Enter centre number: ",
        "Invalid centre, please try again"
    ),
    "Candidates": (
        "Enter the first and last candidate number (for example '1 10' for 10 candidates): ",
        "Invalid candidate range, please try again"
    ),
    "QPV": (
        "Enter QPV for ",
        "QPV can only be numerical, please try again"
    ),
    "Mark Scheme": (
        "Choose an option from the following list:\n\
        1: Use full marks for all candidates\n\
        2: Use random marks for all candidates\n\
        3: Use specific marks for each module but shared by candidates\n\
        4: Choose individual marks for each candidate and module\n",
        "Invalid option entered, please try again"
    )
}


def get_pos() -> str:
    """Take and validate POS input.

    Returns:
        str: Validated POS
    """
    while True:
        prompt, repeat = MESSAGE_DICT["POS"]
        pos = input(prompt).upper()
        if pos not in POS_CODES["Programme of Study Code"].unique():
            print(repeat)
            continue
        return pos


def get_kad() -> str:
    """Take and validate KAD input.

    Returns:
        str: Validated KAD
    """
    while True:
        prompt, repeat = MESSAGE_DICT["KAD"]
        user_input = input(prompt).upper()
        try:
            kad = datetime.strptime(user_input, "%d/%m/%Y")
        except ValueError:
            print(repeat)

            continue
        return datetime.strftime(kad, "%d/%m/%Y")


def get_sitting() -> str:
    """Take and validate sitting input.

    Returns:
        str: Validated sitting
    """
    while True:
        prompt, repeat = MESSAGE_DICT["Sitting"]
        sitting = input(prompt).upper()
        if sitting not in ["AM", "PM", "EV"]:
            print(repeat)
            continue
        return sitting


def get_centre() -> str:
    """Function to take and validate centre input.

    Returns:
        str: validated centre
    """
    return validate_match(key='Centre')


def get_candidates() -> range:
    patt = REGEX_PATTERNS["Candidates"]
    while True:
        prompt, repeat = MESSAGE_DICT["Candidates"]
        candidates = input(prompt).upper()
        candidates = candidates.strip()
        match = patt.match(candidates)
        if not match:
            print(repeat)
            continue
        min_cand = int(match.groupdict()["min_cand"])
        max_cand = int(match.groupdict()["max_cand"])
        if max_cand < min_cand:
            print(repeat)
            continue
        return range(min_cand, max_cand + 1)


def validate_match(key) -> str:
    regex_pattern = REGEX_PATTERNS[key]
    prompt, repeat = MESSAGE_DICT[key]
    while True:
        user_input = input(prompt).upper()
        if not regex_pattern.match(user_input):
            print(repeat)
            continue
        return user_input


def get_qpvs(candidates: range, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    REGEX_PATTERNS["QPV"]
    for module in df['Module Code'].unique():
        qpv = validate_match(key='QPV')
        for cand in candidates:
            # Put entered mark into each row
            df.loc[
                (df["Module Code"] == module) & (df["Candidate No"] == cand),
                "Module Question Paper Version",
            ] = qpv
    return df


def add_details_to_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Assessment Event Date'], df['Assessment Event Sitting'], df['Centre No'] = get_kad(), get_sitting(), get_centre()
    return df


def mark_scheme() -> int:
    return int(validate_match(key='Mark Scheme'))


def validate_mark(max_mark: int, input_question: str):
    mark_columns = {'Present': 'Candidate Mark',
                    'Absent': 'Candidate Status'}
    while True:
        mark = input(input_question).upper()
        if mark == "A":
            return mark, mark_columns['Absent']
        elif mark.isnumeric():
            if int(mark) <= max_mark and int(mark) >= 0:
                return mark, mark_columns['Present']
            else:
                print("Mark given is outside valid range, please try again")
        else:
            try:
                float(mark)
                if float(mark) <= max_mark and float(mark) >= 0:
                    return mark, mark_columns['Present']
            except ValueError:
                print("Mark given is outside valid range, please try again")


def assign_marks(df: pd.DataFrame, option: int) -> pd.DataFrame:
    """_summary_

    Args:
        df (pd.DataFrame): _description_
        option (int): _description_

    Returns:
        pd.DataFrame: _description_
    """
    df = df.copy()
    if option == 1:
        # Set candidate mark as the maximum mark
        df["Candidate Mark"] = df["Max_Mark"]

    elif option == 2:
        # Enter a random mark for each row within range of max mark
        df["Candidate Mark"] = df["Max_Mark"].apply(lambda x: randint(0, x))

    elif option == 3:
        # Get each distinct module code
        print(df["Module Code"].unique())
        # Loop distinct module codes to assign a mark to all rows matching that module
        for module in df['Module Code'].unique():
            # Get the maximum possible mark for that module
            max_mark = df[df['Module Code'] == module]['Max_Mark'].to_list()[0]
            input_question = f"Enter mark for {module} (max: {max_mark}): "
            mark, mark_column = validate_mark(max_mark, input_question)
            # Put entered mark into each row
            df.loc[df['Module Code'] == module, mark_column] = mark

    elif option == 4:
        for idx, row in df.iterrows():
            # Get the maximum possible mark for that row
            max_mark = row['Max_Mark']
            input_question = (
                f"Enter mark for {row['Module Code']}\
                {row['Measure Def Code']}\
                {row['Candidate No']}\
                (max: {max_mark}): ")
            mark, mark_column = validate_mark(max_mark, input_question)
            df.loc[idx, mark_column] = mark

    return df


def add_candidates_to_df(
    candidates: range, df: pd.DataFrame, candidate_df: pd.DataFrame
        ) -> pd.DataFrame:
    # For each candidate in the range of candidates given add candidate number
    # to a new column in dataframe
    for cand in candidates:
        temp_df = df.copy()
        temp_df["Candidate No"] = cand
        # Concatenate the dataframe for each candidate
        candidate_df = pd.concat([candidate_df, temp_df], ignore_index=True)
    candidate_df["Max_Mark"] = candidate_df["Max_Mark"].astype(np.uint8)
    return candidate_df


def get_qpvs_for_candidates(pos_df: pd.DataFrame, candidate_df: pd.DataFrame) -> pd.DataFrame:
    # create an empty dataframe to store data for all candidates
    choice = "y"
    while choice == "y":
        candidates = get_candidates()
        candidate_df = add_candidates_to_df(
            candidates=candidates, df=pos_df, candidate_df=candidate_df
        )
        # Take QPV from user and add to dataframe
        candidate_df = get_qpvs(candidates, candidate_df)
        choice = input("Would you like to add another candidate range? y/n:")
    return candidate_df


def save_df_to_csv(df: pd.DataFrame):
    # Drop Max Marks column for output csv
    df = df.drop(columns=['Max_Mark'])

    # Get file name inputs from df
    kad, pos, centre, sitting = (str(
        df['Assessment Event Date'].unique()[0]),
        df['Programme of Study Code'].unique()[0],
        df['Centre No'].unique()[0],
        df['Assessment Event Sitting'].unique()[0])

    # Convert int style candidate number to 0000 format
    df['Candidate No'] = df['Candidate No'].apply(lambda x: f"{x:>04}")

    # Remove invalid filepath symbols
    file_kad = kad.replace("/", "")

    # Save df to CSV with filename using session details
    df.to_csv(str(MARKSFOLDER) + f'\\marksfile_{pos}_{centre}_{file_kad}{sitting}.csv', index=False)


def input_choice() -> str:
    return input(
        "How would you like to enter data? \n\
        1. Enter in format (POS) (KAD) (Sitting) (Centre)\n\
        2. Enter separately\n"
    )


def main() -> None:
    # Repeat program while user wants to create more files
    choice = "Y"
    while choice == "Y":

        os.system("cls" if os.name == "nt" else "clear")

        # Create empty dataframe which will become our output file
        candidate_df = pd.DataFrame(columns=HEADER)

        print("Marks file creation program")

        # Slice df and add the provided details
        pos_df = POS_CODES[POS_CODES['Programme of Study Code'] == get_pos()].copy()
        pos_df = add_details_to_df(pos_df)
        candidate_df = get_qpvs_for_candidates(pos_df=pos_df, candidate_df=candidate_df)

        # Ask how the user would like to add marks
        marking_choice = mark_scheme()

        # Add marks to each candidate
        candidate_df = assign_marks(candidate_df, marking_choice)
        save_df_to_csv(candidate_df)

        # Keep repeating until no
        choice = input("Generate another marks file? y/n:").upper()


if __name__ == "__main__":
    main()
