import os
from . import Records
from ..models import db_operation, db_proxy as db
from ..models.api import API
from .. import custom_halo
from ..core_logging import logger


def parse_api_key_file(filepath: str) -> dict[str, str]:
    """Reads and parses the API key information from provided file

    Args:
        filepath (str): Path to the file containing API key information.

    Returns:
        dict: A dictionary representing a record to be added to the API table.

    Note:
        The file must have the following keys: `organization`, `api_key`,
            `can_edit`, `can_view`, and `date_generated`
    """
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    record = {}
    keys = ["organization", "api_key", "can_edit", "can_view"]
    for line in lines:
        key, value = line.strip().split(": ", 1)
        key = key.lower().replace(" ", "_")  # convert API Key to api_key, etc.
        if key in keys:
            if "can_" in key:
                record[key] = value.lower() == "true"
            record[key] = value
        else:
            logger.debug(f"{key} is not a valid api field.")

    return record


@custom_halo(text="Creating api key table records")
def create_api_key_table_records(api_keys_dir: str = "./data/API") -> Records:
    """Parses the given directory and associates each api_key with it's
    information.

    Args:
        api_keys_dir (str): relative path to api key direcotry.
            Default `./data/API`

    Return:
        Records: Records to be added to the API table
    """

    records = []

    for file in os.listdir(api_keys_dir):

        full_file_path = os.path.join(api_keys_dir, file)

        record = parse_api_key_file(full_file_path)
        records.append(record)

    return records


@custom_halo(text="Updating api key table")
@db_operation("edit")
def update_api_key_table(api_key_records: Records) -> None:
    """Adds data to the API table in the database.

    In cases where the api_key is already in teh table, it updates the data for
    that row

    Args:
        api_key_records (Records): Records of rows to be added to the table

    """
    with db.atomic():
        API.insert_many(api_key_records).on_conflict(
            conflict_target=[API.api_key],
            preserve=[API.organization, API.can_edit, API.can_view, API.date_generated],
        ).execute()


if __name__ == "__main__":
    data = create_api_key_table_records()
    print(data)
    # update_api_key_table(data)
