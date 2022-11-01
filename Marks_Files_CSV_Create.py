"""Functionality to automate marking CSV file generation."""


import os
import re
from datetime import datetime
from pathlib import Path
from random import randint
from typing import List

import numpy as np
import pandas as pd


FILEPATH = Path("Marks_Files")
FILEPATH.mkdir(parents=True, exist_ok=True)

POS_CODES = pd.read_csv("POS_Codes.csv")
HEADER = [
    "Purchase Order Number",
    "Item Number",
    "Centre No",
    "Centre No (SAP)",
    "Candidate No",
    "Candidate No (SAP)",
    "ATA Candidate Number",
    "Programme of Study Code",
    "Module Code",
    "Module Booking GUID",
    "Assessment Event Date",
    "Assessment Event Sitting",
    "Module Question Paper Version",
    "Candidate Status",
    "Measure Def Code",
    "Measure Def Desc",
    "Measure Def Level",
    "Candidate Mark",
    "Examiner Id (UCLES ID)",
    "Delivery Method",
]


def get_pos() -> str:
    """Function to take and validate POS input.

    Returns:
        str: Validated POS
    """
    while True:
        pos = input("Enter POS (in format D###): ").upper()
        if pos not in POS_CODES["Programme of Study Code"].unique():
            print("Invalid POS, please try again")
            continue
        return pos


def get_kad() -> str:
    """Function to take and validate KAD input.

    Returns:
        str: Validated KAD
    """
    while True:
        user_input = input("Enter KAD (in format DD/MM/YYYY): ").upper()
        try:
            kad = datetime.strptime(user_input, "%d/%m/%Y")
        except ValueError:
            print("Invalid date given, try again")
            continue
        return datetime.strftime(kad, "%d/%m/%Y")


def get_sitting() -> str:
    """Function to take and validate sitting input.

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
    """Function to take and validate centre input.

    Returns:
        str: validated centre
    """
    valid_patts = [re.compile(r"^[\d]{5}$"), re.compile(r"^[A-Z]{2}[\d]{3}$")]
    match_question = "Enter centre number: "
    error_message = "Invalid centre, please try again"
    return validate_match(
        regex_pattern=valid_patts,
        match_question=match_question,
        error_message=error_message,
    )


def get_candidates() -> range:
    patt = re.compile(r"^(?P<min_cand>[1-9][\d]*)[\s]+(?P<max_cand>[1-9][\d]*)$")
    while True:
        candidates = input(
            "Enter the first and last candidate number"
            "(for example '1 10' for 10 candidates): "
        )
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


def validate_match(
    regex_pattern: List[re.Pattern], match_question: str, error_message: str
) -> str:
    patts = regex_pattern
    while True:
        user_input = input(match_question).upper()
        if not any([patt.match(user_input) for patt in patts]):
            print(error_message)
            continue
        return user_input


def get_qpvs(candidates: range, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    valid_patts = [re.compile(r"^[\d]*$")]
    for module in df["Module Code"].unique():
        match_question = f"Enter QPV for {module}: "
        error_message = "QPVs can only contain numeric digits, please try again"
        qpv = validate_match(
            regex_pattern=valid_patts,
            match_question=match_question,
            error_message=error_message,
        )
        for cand in candidates:
            # Put entered mark into each row
            df.loc[
                (df["Module Code"] == module) & (df["Candidate No"] == cand),
                "Module Question Paper Version",
            ] = qpv
    return df


def add_details_to_df(df: pd.DataFrame, kad, sitting, centre) -> pd.DataFrame:
    df = df.copy()
    df["Assessment Event Date"], df["Assessment Event Sitting"], df["Centre No"] = (
        kad,
        sitting,
        centre,
    )
    return df


def mark_scheme() -> int:
    option_patt = re.compile("^[1-4]$")
    while True:
        choice = input(
            "Choose an option from the following list:\n\
            1: Use full marks for all candidates\n\
            2: Use random marks for all candidates\n\
            3: Use specific marks for each module but shared by candidates\n\
            4: Choose individual marks for each candidate and module\n"
        )
        match = option_patt.match(choice)
        if not match:
            print("Invalid option entered, please try again")
            continue
        return int(choice)


def validate_mark(mark: str, max_mark: int) -> bool:
    if not mark:
        return True
    elif mark.isnumeric() and int(mark) <= max_mark and int(mark) >= 0:
        return True
    else:
        return False


def assign_marks(df: pd.DataFrame, option: int) -> pd.DataFrame:
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
        df["Candidate Mark"] = df["Max_Mark"]
    elif option == 2:
        # Enter a random mark for each row within range of max mark
        df["Candidate Mark"] = df["Max_Mark"].apply(lambda x: randint(0, x))
    elif option == 3:
        # Get each distinct module code
        print(df["Module Code"].unique())
        for module in df["Module Code"].unique():
            # Get the maximum possible mark for that module
            max_mark = df[df["Module Code"] == module]["Max_Mark"].to_list()[0]
            while True:
                # Get user to enter mark for module
                mark = input(f"Enter mark for {module} (max: {max_mark}): ")
                valid_mark = validate_mark(mark, max_mark)
                if not valid_mark:
                    print("Mark given is outside valid range, please try again")
                    continue
                # Put entered mark into each row
                df.loc[df["Module Code"] == module, "Candidate Mark"] = mark
    elif option == 4:
        for idx, row in df.iterrows():
            # Get the maximum possible mark for that row
            max_mark = row["Max_Mark"]
            while True:
                # Get mark from user input
                mark = input(
                    f"Enter mark for {row['Module Code']} {row['Measure Def Code']} {row['Candidate No']} (max: {max_mark}): "
                )
                valid_mark = validate_mark(mark, max_mark)
                if not valid_mark:
                    print("Mark given is outside valid range, please try again")
                    continue
                df.loc[idx, "Candidate Mark"] = mark
                break
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


def get_qpvs_for_candidates(pos_df) -> pd.DataFrame:
    # create an empty dataframe to store data for all candidates
    candidate_df = pd.DataFrame(columns=HEADER)
    choice = "y"
    while choice == "y":
        candidates = get_candidates()
        candidate_df = add_candidates_to_df(
            candidates=candidates, df=pos_df, candidate_df=candidate_df
        )
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
    df = df.drop(columns=["Max_Mark"])
    kad, pos, centre, sitting = (
        df["Assessment Event Date"].unique(),
        df["Programme of Study Code"].unique(),
        df["Centre No"].unique(),
        df["Assessment Event Sitting"].unique(),
    )

    kad, pos, centre, sitting = str(kad[0]), pos[0], centre[0], sitting[0]

    df["Candidate No"] = df["Candidate No"].apply(lambda x: f"{x:>04}")
    # Remove invalid filepath symbols
    file_kad = kad.replace("/", "")
    # Save df to CSV with filename using session details
    df.to_csv(
        str(FILEPATH) + f"\marksfile_{pos}_{centre}_{file_kad}{sitting}.csv",
        index=False,
    )


def input_choice() -> str:
    return input(
        "How would you like to enter data? \n\
        1. Enter in format (POS) (KAD) (Sitting) (Centre)\n\
        2. Enter separately\n"
    )


def main() -> None:
    choice = "y"
    while choice == "y":
        os.system("cls" if os.name == "nt" else "clear")
        print("Marks file creation program")
        # Take session details from user
        pos = get_pos()
        kad = get_kad()
        sitting = get_sitting()
        centre = get_centre()
        # Slice df and add the provided details
        pos_df = POS_CODES[POS_CODES["Programme of Study Code"] == pos].copy()
        pos_df = add_details_to_df(pos_df, kad, sitting, centre)
        candidate_df = get_qpvs_for_candidates(pos_df=pos_df)
        save_df_to_csv(candidate_df)
        choice = input("Generate another marks file? y/n:")


if __name__ == "__main__":
    main()
