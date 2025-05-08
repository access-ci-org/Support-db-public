import os
import pandas as pd
from pandas._libs.parsers import STR_NA_VALUES
from core.db_logic import Records
from core.models import db_operation, db_proxy as db
from core.models.software import Software
from core.models.aiSoftwareInfo import AISoftwareInfo
from core import custom_halo
from core.core_logging import logger


def lowercase_file_names(dir_path: str) -> None:
    """Converts all file names in a given directory to lowercase.
    Args:
        dir_path (str): path to the directory where the files are located
    """
    for file in os.listdir(dir_path):
        os.rename(dir_path + file, dir_path + file.lower())


EXAMPLE_USE_DIR = "./data/exampleUse/"


def add_ai_example_use_to_df(
    df: pd.DataFrame, software_column_name: str
) -> pd.DataFrame:
    """Matches software name with example use file from the EXAMPLE_USE_DIR

    Adds example use info to the given df

    Args:
        df (pandas.DataFrame): dataframe with an empty ai_example_use column and
            some software column that has software names
    Returns:
        pandas.DataFrame: DataFrame with filled ai_example_use column

    Note:
        This function is called directly from create_ai_software_table_records.
    """
    software_names = df[software_column_name].tolist()

    # All softwares are lowercased so files should be lowercased to match
    lowercase_file_names(EXAMPLE_USE_DIR)

    for software in software_names:
        software_file_path = f"{EXAMPLE_USE_DIR}/{software}.txt"
        try:
            with open(software_file_path, "r", encoding="utf-8") as s:
                data = s.read()
                df.loc[df[software_column_name] == software, "ai_example_use"] = data

        except FileNotFoundError:
            logger.info(
                f"No example use file found for {software} in {EXAMPLE_USE_DIR}"
            )
            continue

    return df


# TODO: This is a temporary function that gets data from the csv file.
#   Should be changed to get data directly from the stuff in the `data`
#   directory
@custom_halo(text="Creating ai software table records")
def create_ai_software_table_records(
    columns: list = None, software_table_csv: str = "./data/CSV/softwareTable.csv"
) -> Records:
    """Creates 'records' of ai software info to add to the database.

    Each record uses the information from the software_table_csv file. The AI
    example use is added using the information from the data folder. The columns
    are renamed to match the AISoftwareInfo table.

    Args:
        columns (list): A list of columns in the software_table_csv file that we
            want to keep.
        software_table_csv (str): Path to the software_table csv

    Returns:
        Records: list of records to be added to the Software table.
            The keys of the dict are columns in the table.
    Note:
        Calls the `add_ai_example_use_to_df` function
    """

    try:
        # Ookami has a software called 'null'...
        # the code below tells pandas to not treat 'null' as NaN or NULL value

        # Get the default list of NA values
        default_na_values = list(STR_NA_VALUES)
        custom_na_values = [v for v in default_na_values if v != "null"]
        df = pd.read_csv(
            software_table_csv, keep_default_na=False, na_values=custom_na_values
        )

    except Exception as e:
        logger.debug("Software table not found")
        logger.debug(e)
        return None

    if columns:
        current_df_columns = set(df.columns.tolist())
        # get list of columns not in `columns`
        columns_to_remove = list(current_df_columns - columns)

        df = df.drop(columns=columns_to_remove)

    # rename the columns to match the db software table columns
    df = df.rename(
        columns={
            "✨Software Type": "ai_software_type",
            "✨Software Class": "ai_software_class",
            "✨Research Field": "ai_research_field",
            "✨Research Area": "ai_research_area",
            "✨Research Discipline": "ai_research_discipline",
            "✨Core Features": "ai_core_features",
            "✨General Tags": "ai_general_tags",
            "✨AI Description": "ai_description",
            "✨Example Use": "ai_example_use",
        }
    )

    df = add_ai_example_use_to_df(df, "Software")

    # Replace software names with software id
    software_names = df["Software"].tolist()

    for s in software_names:
        software_id = Software.get(Software.software_name == s)
        df.Software = df.Software.replace(s, software_id)
    df = df.rename(columns={"Software": "software_id"})

    df = df.fillna("")

    ai_software_records = df.to_dict("records")
    return ai_software_records


@custom_halo(text="Updating ai software table")
@db_operation("edit")
def update_ai_software_table(ai_software_records: Records) -> None:
    """Update ai_software_table from given records

    Args:
        ai_software_records (Records): Records of ai software data to be added
            to the database.

    Notes:
        In case of conflicting entries it will always use the newest data.
    """

    with db.atomic():
        AISoftwareInfo.insert_many(ai_software_records).on_conflict(
            # If there is a conflict on the `Unique` constraint of software_id
            conflict_target=[AISoftwareInfo.software_id],
            # Update the existing ai_software entry using the incomming data
            preserve=[
                AISoftwareInfo.ai_description,
                AISoftwareInfo.ai_software_type,
                AISoftwareInfo.ai_software_class,
                AISoftwareInfo.ai_research_field,
                AISoftwareInfo.ai_research_area,
                AISoftwareInfo.ai_research_discipline,
                AISoftwareInfo.ai_core_features,
                AISoftwareInfo.ai_general_tags,
                AISoftwareInfo.ai_example_use,
            ],
        ).execute()


if __name__ == "__main__":
    pass
