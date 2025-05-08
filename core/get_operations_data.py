import requests
from pathlib import Path
import json
import pandas as pd
from operations_report import run
from core.parse_ipf_software import parse_ipf_software


def get_data_by_rp(data: pd.DataFrame, resource_name: str):
    df = data[data['ResourceID'].str.startswith(resource_name)]
    return df

def get_and_parse_operations_software_data(
    operations_save_file: str = 'data/operations_data.json',
    parsed_save_file: str = "data/parsed_software.json"
) -> list[dict]:
    operations_save_file = Path(operations_save_file)

    try:
        # run code provided by operations and save result to file
        run(operations_save_file)

        # read operations data from saved file, parse it for what we need and save it
        parse_ipf_software(operations_save_file, output_file=parsed_save_file)
        with open(parsed_save_file, 'r')as psf:
            data = json.load(psf)
        return data
    except Exception as e:
        raise e


def combine_versions(data: dict) -> list:
    """Groups software and combines all versions under one entry."""
    software_dict = {}

    rp_software_groups= {}

    for resource_id in data:
        rp_software_groups['rp_id'] = resource_id
        rp_software_groups['software'] = {}

    for entry in data:
        app_name = entry.get("AppName", "Unknown")
        app_version = entry.get("AppVersion", "Unknown")

        if not app_name:
            continue  # Skip entries with no AppName

        # If the software is already in the dictionary, add the version, otherwise create a new entry
        if app_name in software_dict:
            if app_version not in software_dict[app_name]["Versions"]:
                software_dict[app_name]["Versions"].append(app_version)
            software_dict[app_name]["Entries"].append(entry)
        else:
            software_dict[app_name] = {
                "AppName": app_name,
                "Versions": [app_version],
                "Entries": [entry]
            }

    return list(software_dict.values())

# Get and load operations data
def import_operations_data():
    # print("Retrieving data from Operations API...")
    operations_save_file = './data/operations_data.json'
    parsed_save_file = "data/parsed_software.json"
    # print(operations_save_file)
    data = get_and_parse_operations_software_data(
        operations_save_file=operations_save_file,
        parsed_save_file=parsed_save_file
        )

    if not data:
        print("No data retrieved, exiting.")
        exit()
