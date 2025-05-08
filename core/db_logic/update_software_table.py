import pandas as pd
from pandas._libs.parsers import STR_NA_VALUES  # pylint: disable=no-name-in-module
from . import Records
from ..models import db_operation, db_proxy as db
from ..models.software import Software
from ..retrieve_external_data import get_conda_forge_info
import json
from .. import custom_halo
from ..core_logging import logger

# TODO: This is a temporary function that gets data from the csv file.
#  Should be changed to get data directly from the stuff in the `data` directory

SOFTWARE_TABLE_CSV = "./data/CSV/softwareTable.csv"
COMBINED_DATA = "./data/parsed_software.json"


def load_json_data(json_file):
    """Loads software data from the JSON file."""
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return []


@custom_halo(text="Creating software table records")
def create_software_table_records(
    columns: list,
    # parsed_spider_output: dict[str, list[dict[str, any]]],
    # software_table_csv: str = "./data/CSV/softwareTable.csv",
) -> Records:
    """Creates records of software and related info to add to teh database.

    Each record uses the descriptions, links, and softwares from the
    software_table_csv file. Software is also added from the
    parsed_spider_output and any duplicates are removed.

    Args:
        columns (list):  A list of columns in the software_table_csv file that
            we want to keep.
        parsed_spider_output (dict[str, list[dict[str, any]]]): A dictionary
            with rp name as the key and software information as teh values
            (returned from `parse_spider_output()`)
        software_table_csv (str); Path to the software table csv file
            Default: "./data/CSV/softwareTable.csv"
    Returns:
        Records: Records of data to be added to the Software table. The keys of
            the dict are columns in the table
    """

    try:
        default_na_values = list(STR_NA_VALUES)
        custom_na_values = [v for v in default_na_values if v != "null"]

        df = pd.read_csv(
            SOFTWARE_TABLE_CSV, keep_default_na=False, na_values=custom_na_values
        )

    except Exception as e:
        logger.debug("Software table not found")
        logger.debug(e)

        return None

    # Keep only required columns
    current_df_columns = set(df.columns.tolist())
    columns_to_remove = list(current_df_columns - set(columns))
    df = df.drop(columns=columns_to_remove)

    df = df.rename(
        columns={
            "Software": "software_name",
            "Software Description": "software_description",
            "Software's Web Page": "software_web_page",
            "Software Documentation": "software_documentation",
            "Example Software Use": "software_use_link",
        }
    )

    # Load operations data
    json_data = load_json_data(COMBINED_DATA)
    ipf_software = []
    for _, item in json_data.items():
        ipf_software.extend(item.keys())
    # ipf_software = [software.keys() for software in json_data]
    json_records = [
        {
            "software_name": software,
            "software_description": "",
        }
        for software in ipf_software
    ]
    json_df = pd.DataFrame(json_records)

    # Process spider output
    # spider_software = [item["name"] for rp in parsed_spider_output.values() for item in rp]
    # spider_df = pd.DataFrame(spider_software, columns=["software_name"])

    # Combine sources and ensure case insensitivity
    combined_softwares = (
        pd.concat(
            [df["software_name"].str.lower(), json_df["software_name"].str.lower()]
        )
        .drop_duplicates()
        .reset_index(drop=True)
    )

    software_name_df = pd.DataFrame({"software_name": combined_softwares})

    # Merge CSV and JSON, preventing _x and _y conflicts
    software_df = (
        software_name_df.merge(df, on="software_name", how="left").merge(
            json_df, on="software_name", how="left", suffixes=("", "_json")
        )
    ).fillna("")

    # Resolve software_description conflicts
    if "software_description_json" in software_df.columns:
        software_df["software_description"] = software_df[
            "software_description"
        ].combine_first(software_df.pop("software_description_json"))

    software_records = software_df.to_dict("records")
    return software_records


@custom_halo(text="Updating software table records from external source")
def update_software_records(software_table_records: list[str, any]):
    """
    Update software records with information form external sources such as conda-forge.

    Args:
        software_table_records (list): List of software record dictionaries

    Returns:
        Record: Updated software records
    """
    software = [record["software_name"] for record in software_table_records]
    remote_software_info = get_conda_forge_info(software)
    if not remote_software_info:
        return software_table_records

    for software in software_table_records:
        software_name = software["software_name"]
        if software_name not in remote_software_info:
            continue

        software_info = remote_software_info[software_name]
        remote_details = software_info["about"]

        # Update software description

        if not software.get("software_description", ""):
            description = remote_details.get("description") or remote_details.get(
                "summary"
            )
            if description:
                software["software_description"] = (
                    f"{description.replace('\n', ' ')} "
                    f"Description Source: {software_info['source']}"
                )

        # Update web page and documentation URLs
        field_mappings = {
            "software_web_page": "home",
            "software_documentation": "doc_url",
        }

        for local_field, remote_field in field_mappings.items():
            if not software[local_field] and remote_details.get(remote_field):
                software[local_field] = remote_details[remote_field]

    return software_table_records


@custom_halo(text="Updating software table")
@db_operation("edit")
def update_software_table(software_records: Records) -> None:
    """Adds data to the Software table based on provided software_records.

    In cases where the software_name is already in the table, it updates the
    data for that row.

    Args:
        software_records: Records where each key in the dict is a column in the
            RPS table (returned from `create_software_table_records()`)
    """
    with db.atomic():
        for record in software_records:
            rows_affected = (
                Software.insert(**record)
                .on_conflict(
                    conflict_target=[Software.software_name],
                    update={
                        Software.software_description: record["software_description"],
                        Software.software_web_page: record["software_web_page"],
                        Software.software_documentation: record[
                            "software_documentation"
                        ],
                        Software.software_use_link: record["software_use_link"],
                    },
                )
                .execute()
            )
            if not rows_affected:
                logger.info(f"Unable to add item for: {record}")


if __name__ == "__main__":
    pass
