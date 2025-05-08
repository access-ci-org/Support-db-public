from ..models import db_operation, db_proxy as db
from ..models.rpSoftware import RPSoftware
from ..models.software import Software
from ..models.rps import RPS
from ..models.aiSoftwareInfo import AISoftwareInfo
import pandas as pd
import operator
from functools import *
import re
from peewee import ModelSelect, Expression


@db_operation("view")
def get_software_details(software_names: str, query: ModelSelect) -> ModelSelect:
    """
    Retrieves the details of a software or multiple software entries from the database using Peewee query filtering.

    Args:
        software_names (str): The software name(s) to search for, separated by the '+' symbol for multiple software queries.
        query (ModelSelect): A Peewee query object containing software data across all Resource Providers (RPs).

    Returns:
        software_data (ModelSelect): Filtered Peewee Query object with the details of the
    """
    software_list = software_names.split("+")

    if not isinstance(query, pd.DataFrame):
        if software_names == "*":  # Get all info for the website
            software_data = query
        else:
            software_data = query.where(
                Software.software_name.in_([name.lower() for name in software_list])
            )

        if not software_data.exists():
            return None  # Returning None to indicate that no match was found

        return software_data
    else:
        if software_names == "*":  # Get all info for the website
            software_data = query
        else:
            software_data = query[
                query["software_name"]
                .str.lower()
                .isin([name.lower() for name in software_list])
            ]

        if software_data.empty:
            return None  # Returning None to indicate that no match was found

        return software_data


@db_operation("view")
def get_rp_details(rp_names: str, query: ModelSelect) -> ModelSelect:
    """
    Retrieves the details of an RP or multiple RPs from the database using Peewee query filtering.

    Args:
        rp_names (str): The RP name(s) to search for, separated by the '+' symbol for multiple RP queries.
        query (ModelSelect): A Peewee query object containing RP data across all software entries.

    Returns:
        rp_data (ModelSelect): Filtered Peewee Query object with the details of the requested RP(s), or None if no match is found.

    """
    rp_list = [name.lower() for name in rp_names.split("+")]
    # Check due to API_0 and API_0v1 working with different query objects
    if not isinstance(query, pd.DataFrame):
        rp_data = query.where(
            (RPS.rp_name.in_(rp_list)) | (RPS.rp_group_id.in_(rp_list))
        )

        if not rp_data.exists():
            return None  # Returning None to indicate that no match was found
        return rp_data
    else:
        rp_data = query[
            query["rp_name"].str.lower().isin([name.lower() for name in rp_list])
            | query["rp_group_id"].str.lower().isin([name.lower() for name in rp_list])
        ]

        if rp_data.empty:
            return None  # Returning None to indicate that no match was found
        return rp_data


@db_operation("view")
def search_software(search: str) -> ModelSelect:
    """
    Column-specific search. Extracts software from the database based on column-specific searches in the form of:
    col_name(value).

    Args:
        search (str): The string containing key(value) pairs to search for.
            Filters inner-join by '&' and union by the '+'.

    Returns:
        (query object): Filtered query with the details of the requested search parameters, or an empty query if no match is found.

    Examples:
        rp_name(ookami)&software_name(7z)+rp_name(anvil)
        The above query returns software named 7z on ookami and all software on anvil.

    """
    search_groups = find_search_groups(search)

    filters = []

    for search in search_groups:
        filter = build_filtered_query(search)
        filters.append(filter)

    ored_filters = reduce(operator.or_, filters)

    query = (
        RPSoftware.select(RPSoftware, Software, RPS, AISoftwareInfo)
        .join(Software, on=(RPSoftware.software_id == Software.id))
        .join(RPS, on=(RPSoftware.rp_id == RPS.id))
        .left_outer_join(AISoftwareInfo, on=(AISoftwareInfo.software_id == Software.id))
    ).where(ored_filters)

    if not query.exists():
        return None

    return query


def build_filtered_query(search_group: dict) -> Expression:
    """
    Takes a search group and returns a filter to be used in a database query.

    Args:
        search_group (dict): Key value pairs. Keys are columns in the database and a value is the value to be searched for in the column.

    Returns:
        anded_filters (Expression): Filters with logical & between them.

    Examples:
        If your current search group is {'rp_name': 'ookami', 'software_name': '7z'}.
        Then this function returns a filter that finds rows in the DB that have ookami in rp_name AND 7z in software_name.
    """

    # Define a mapping of keys to their corresponding model and field
    field_map = {
        "software_name": (Software, Software.software_name),
        "software_description": (Software, Software.software_description),
        "software_web_page": (Software, Software.software_web_page),
        "software_documentation": (Software, Software.software_documentation),
        "software_use_link": (Software, Software.software_use_link),
        "rp_name": (RPS, RPS.rp_name),
        "rp_group_id": (RPS, RPS.rp_group_id),
        "ai_description": (AISoftwareInfo, AISoftwareInfo.ai_description),
        "ai_software_type": (AISoftwareInfo, AISoftwareInfo.ai_software_type),
        "ai_software_class": (AISoftwareInfo, AISoftwareInfo.ai_software_class),
        "ai_research_field": (AISoftwareInfo, AISoftwareInfo.ai_research_field),
        "ai_research_area": (AISoftwareInfo, AISoftwareInfo.ai_research_area),
        "ai_research_discipline": (
            AISoftwareInfo,
            AISoftwareInfo.ai_research_discipline,
        ),
        "ai_core_features": (AISoftwareInfo, AISoftwareInfo.ai_core_features),
        "ai_general_tags": (AISoftwareInfo, AISoftwareInfo.ai_general_tags),
        "ai_example_use": (AISoftwareInfo, AISoftwareInfo.ai_example_use),
        "software_versions": (RPSoftware, RPSoftware.software_versions),
        "rp_software_documentation": (RPSoftware, RPSoftware.rp_software_documentation),
    }

    # Apply filters dynamically based on the dictionary passed in
    filters = []
    for key, value in search_group.items():
        if key in field_map:
            model, field = field_map[key]
            # Only keep items that contain value in specific column
            filters.append(field.contains(value))

    # AND all of the filters together
    anded_filters = reduce(operator.and_, filters)

    return anded_filters


def find_search_groups(search: str) -> list:
    """
    Parses the search string into a list of dictionaries containing key-value pairs of the DB columns and values to search for.

    Args:
        search (str): The search string grabbed from the API url

    Returns:
        search_groups (list): A list of dictionaries containing key-value pairs associated with the column-specific search
    """
    intersect_groups = {}
    # intersect_groups stores a dictionary
    # key: idx
    # value: grouped searches
    for idx, group in enumerate(search):
        intersect_groups[idx] = re.split(r"&(?![^\(]*\))", group)

    # search_groups stores parsed searches
    # i.e. intersect_group[0] holds [rp_name(anvil), software_name(abacas)]
    # search_group[0] then holds [{'rp_name: 'anvil', 'software_name': 'abacas'}]
    search_groups = []

    for group in intersect_groups.values():
        search_columns = {}
        for item in group:
            # Split the string into key and value
            key, value = item.split("(")
            value = value.rstrip(")")  # Remove the closing parenthesis from the value

            # Add the key-value pair to the dictionary
            search_columns[key] = value

        search_groups.append(search_columns)

    return search_groups
