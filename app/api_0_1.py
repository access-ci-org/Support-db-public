from flask import Flask, jsonify, request, Response, make_response
from flask_restful import Resource
from functools import wraps
import pandas as pd
import re
from core.models import view_db, db_operation, db_proxy as db
from core.models.rpSoftware import RPSoftware
from core.models.software import Software
from core.models.rps import RPS
from core.models.aiSoftwareInfo import AISoftwareInfo
from core.models.api import API
from core.db_logic.get_software_details import get_software_details, get_rp_details, search_software


# API key validation
@db_operation('view')
def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = kwargs.get('api_key') or request.view_args.get('api_key')

        with db.atomic():
            # Query the database to check if the provided API key exists
            api_key_exists = API.select().where(API.api_key == api_key).exists()

        if not api_key_exists:
            # If the API key does not exist, return an error response
            return make_response(({'message': 'Invalid or missing API key'}), 401)
        return func(*args, **kwargs)
    return decorated_function

class API_0_1(Resource):
    """
       API_0_1 Class
       This class provides the core functionality for version 1 of the API,
       enabling refined data retrieval and filtering for software and RP
       (Resource Provider) information. This version introduces search and
       filtering enhancements, allowing more complex queries and column
       management for customized output.

       Features:
           - Allows searching for software, RPs, and specific attributes
             (via the `search` parameter), enhancing flexibility.
           - Supports inclusion/exclusion of specific columns, while
             ensuring key fields like `software_name`, `rp_name`, and
             `rp_group_id` are always included.
           - Orders output data alphabetically by `software_name`, and
             organizes the fields according to a specified structure.
           - Returns data in multiple formats: JSON, CSV, or HTML, depending
             on the user’s request.
    """
    def __init__(self):
        """
        Initializes the API_0_1 class by loading all software and
        RP data from the database into a Peewee ModelSelect object.
        """
        self.query = self.load_tables()

    @require_api_key
    def get(self, query, api_key=None):
        try:
            params = dict(item.split('=') for item in query.split(','))
            software_names = params.get('software')
            rp_names = params.get('rp')
            searchString = params.get('search', '')
            search = re.findall(r'(\w+\s*\(.*?\)(?:&\w+\s*\(.*?\))*)(?=\s*\+|$)', searchString)
            exclude_columns = set(filter(None, params.get('exclude', '').split('+')))
            include_columns = set(filter(None, params.get('include', '').split('+')))
            response_type = params.get('type', 'json').lower()

            # Handle software search
            if software_names:
                query = get_software_details(software_names, self.query)
            # Handle RP search
            elif rp_names:
                query = get_rp_details(rp_names, self.query)
            elif search:
                query = search_software(search)
            else:
                return make_response(({'message': 'Invalid request parameters'}), 400)


            # If no data found, handle the error
            if query is None:
                return make_response({'message': 'No data found'}, 404)

            # Convert query result to a list of dictionaries
            query = list(query.dicts())

            # Define column inclusion/exclusion
            grouped_data = {}

            for row in query:
                software_name = row['software_name']
                if software_name not in grouped_data:
                    grouped_data[software_name] = {
                        'software_name': software_name,
                        'software_description': row['software_description'],
                        'ai_description': row['ai_description'],
                        'ai_core_features': row['ai_core_features'],
                        'software_documentation': row['software_documentation'],
                        'ai_software_type': row['ai_software_type'],
                        'ai_research_area': row['ai_research_area'],
                        'ai_research_discipline': row['ai_research_discipline'],
                        'ai_general_tags': row['ai_general_tags'],
                        'software_web_page': row['software_web_page'],
                        'ai_research_field': row['ai_research_field'],
                        'software_use_link': row['software_use_link'],
                        'ai_software_class': row['ai_software_class'],
                        'ai_example_use': row['ai_example_use'],
                        'rp_name': [],
                        'rp_group_id': [],
                        'rp_software_documentation': [],
                        'software_versions': []
                    }

                # Append RP-specific information to lists
                grouped_data[software_name]['rp_name'].append(row['rp_name'])
                grouped_data[software_name]['rp_group_id'].append(row['rp_group_id'])
                grouped_data[software_name]['rp_software_documentation'].extend(
                    self.format_software_info([row], [row['rp_software_documentation']])
                )
                grouped_data[software_name]['software_versions'].extend(
                    self.format_software_info([row], [row['software_versions']])
                )

            # Apply include/exclude columns to filtered data
            essential_columns = {'software_name', 'rp_name', 'rp_group_id'}
            if include_columns:
                include_columns = include_columns.union(essential_columns)
                filtered_data = [
                    {col: row[col] for col in row if col in include_columns}
                    for row in grouped_data.values()
            ]
            elif exclude_columns:
                filtered_data = [
                    {col: row[col] for col in row if col not in exclude_columns}
                    for row in grouped_data.values()
            ]
            else:
                filtered_data = list(grouped_data.values())

            # rp name and rp_groups are duplicated becuase multiple rp_resource_ids have
            #   the same software so the following will de-duplicate them
            print(filtered_data[0])
            for item in filtered_data:
                if "rp_name" in item:
                    item["rp_name"] = sorted(list(set(item["rp_name"])))
                if "rp_group_id" in item:
                    item["rp_group_id"] = sorted(list(set(item["rp_group_id"])))
                if "rp_software_documentation" in item:
                    item["rp_software_documentation"] = sorted(list(set(item["rp_software_documentation"])))
                if "software_versions" in item:
                    item["software_versions"] = sorted(list(set(item["software_versions"])))

            # Sort `filtered_data` alphabetically by `software_name`
            filtered_data = sorted(filtered_data, key=lambda x: x.get('software_name', ''))

            # Enforce desired column order on the filtered data
            desired_column_order = [
                'software_name', 'rp_name', 'rp_group_id', 'software_description', 'ai_description',
                'ai_core_features', 'software_documentation', 'ai_software_type', 'ai_research_area',
                'ai_research_discipline', 'ai_general_tags', 'software_web_page', 'ai_research_field',
                'software_use_link', 'rp_software_documentation', 'software_versions',
                'ai_software_class', 'ai_example_use'
            ]

            ordered_result_data = [
                {col: item.get(col) for col in desired_column_order if col in item}
                for item in filtered_data
            ]


            # Return as CSV or JSON
            if response_type == 'csv':
                csv_output = pd.DataFrame(ordered_result_data)
                return Response(csv_output.to_csv(index=False), mimetype='text/csv')
            if response_type == 'json':
                return jsonify(ordered_result_data)
            elif response_type == 'html':
                html_output = pd.DataFrame(ordered_result_data)
                return Response(html_output.to_html(index=False), mimetype='text/html')

        except Exception as e:
            print(e)
            return make_response(({'message':'Invalid request parameters'}), 404)

        finally:
            # Close the database connection manually if needed
            if not view_db.is_closed():
                view_db.close()

    def format_software_info(self, query, x):
        """
        Formats and combines `rp_software_documentation` or `software_versions`
        entries for JSON output by pairing each RP name with the respective
        documentation or version info.
        Args:
            query (list): a list of dictionaries, each containing data for a specific
                        RP, including the 'rp_name' field
            x (list): a list of strings representing the 'rp_software_documentation'
                        or 'software_versions' for each RP

        Returns:
            formatted_list (list): a list of strings where each entry is in the format
            'rp_name: info', combining RP names with their respective software
            documentation or version information
        """
        # Takes two iterables (the list of dictionaries `query` and the list `x` containing rp_software_documentation or software_versions).
        # Pairs each dictionary in `query` with the corresponding item in `x`, combining `rp_name` with the documentation or version info.
        # Returns a formatted list of strings in the format "rp_name: info".
        return [f"{row['rp_name']}:    {info}" for row, info in zip(query, x)]


    @db_operation('view')
    def load_tables(self):
        """Gets all available data for all software

        Queries the database using Peewee joins to retrieve comprehensive
        information on software hosted across different Resource Providers (RPs).
        The function performs multiple joins to gather data from related tables
        (e.g., software, RP details, AI software information) and returns it as
        a Peewee query object.

        Returns:
            peewee.ModelSelect: A Peewee Query object containing the joined data
                for all relevant fields across multiple tables, enabling efficient
                access to detailed software and RP information without conversion
                to a DataFrame.

        """
        with db.atomic():
            #Peewee join table query
            query = (RPSoftware.select(RPSoftware,Software, RPS, AISoftwareInfo)
                     .join(Software, on = (RPSoftware.software_id == Software.id))
                     .join(RPS, on = (RPSoftware.rp_id == RPS.id))
                     .left_outer_join(AISoftwareInfo, on = (AISoftwareInfo.software_id == Software.id)))
        return query
