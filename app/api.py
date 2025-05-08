from functools import wraps
from flask import jsonify, request, Response, make_response
from flask_restful import Resource
import pandas as pd
from core.models import view_db, db_operation, db_proxy as db
from core.models.rpSoftware import RPSoftware
from core.models.software import Software
from core.models.rps import RPS
from core.models.aiSoftwareInfo import AISoftwareInfo
from core.models.api import API
from core.db_logic.get_software_details import (
    get_software_details,
    get_rp_details,
    search_software
)
from app.app_logging import logger


# API key validation
@db_operation("view")
def require_api_key(func):
    """Decorator that validates API key exists in database.

    Args:
        func (callable): Function to protect with API key validation

    Returns:
        callable: Decorated function that checks API key before execution.
            Returns 401 response if key is invalid.

    Note:
        API key can be provided via kwargs or request.view_args
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        """Validate API key and execute function if valid.
        Returns:
            any: 401 response if invalid key,
            else function result
        """
        logger.info('Check API key')
        api_key = kwargs.get('api_key') or request.view_args.get('api_key')

        with db.atomic():
            api_match = API.get_or_none(API.api_key == api_key)    # Query the database to check if the provided API key exists
            logger.debug(f"User Organization: {api_match.organization if api_match else api_match}")

        if not api_match:
            logger.error(f'Invalid or missing API key: {api_key}')
            return make_response(({'message': 'Invalid or missing API key'}), 401)  # If the API key does not exist, return an error response
        return func(*args, **kwargs)

    return decorated_function


class Api_0(Resource):
    """Implements functionality for API version 0.

    It processes requests to search for software and RP (Resource Providers),
    filter included/excluded columns, and return the data in various formats
    (JSON, CSV, or HTML). The entire dataset is queried each time a request is
    made, and filtering is applied based on the query parameters.

    Attributes:
        merged_df (pd.DataFrame): A DataFrame of all software information

    ## Methods
        >>> get(query: str, api_key: str = None) -> str | list[dict[str,any]]
        Process API request based on a given query and api_key.
    """

    def __init__(self):
        self.merged_df = self.load_tables()

    @require_api_key
    def get(self, query, api_key=None):
        """Process API request based on a given query and api_key.

        Supports searching for software and RP data, handles column
        inclusion/exclusion, and formats the response accordingly. Uses
        the require_api_key decorator to validate the API key. Returns the
        response in the requested format (JSON, CSV, or HTML).

        Args:
            query (str): User's api query. It must contain either `software=`
                or `rp_name=`.
            api_key (str): User's api_key

        Returns:
            One of the following types:
            * str: A formatted string when response_type is 'HTML' or 'CSV'
                - HTML: "<table><tr>...</tr></table>"
                - CSV: "header1,header2\\nvalue1,value2"
            * dict: A dictionary when response_type is 'JSON' or not specified

        Notes:
            Currently it returns a generic error message when somethign goes
            wrong. TODO: Fix this
            It should return a custom error message based on where the error
            is (user request is bad or somethign internla broke) with any other
            helpful info.
        """

        logger.info(f'Get function on query: {query}')

        try:
            params = dict(item.split("=") for item in query.split(","))
            software_names = params.get("software")
            rp_names = params.get("rp")
            exclude_columns = set(filter(None, params.get("exclude", "").split("+")))
            include_columns = set(filter(None, params.get("include", "").split("+")))
            response_type = params.get("type", "json").lower()

            # Handle software search
            if software_names:
                df = get_software_details(software_names, self.merged_df)
            # Handle RP search
            elif rp_names:
                df = get_rp_details(rp_names, self.merged_df)
            else:
                return make_response(({"message": "Invalid request parameters"}), 400)

            # Check if return value is response (error report)
            if isinstance(df, tuple):
                return make_response(df)  # Return the error response

            # Handle formatting of response
            df = (
                df.groupby("software_name")
                .agg(
                    {
                        "software_name": "first",
                        # Aggregating rp_name into a list
                        "rp_name": lambda x: sorted(list(set(x))),
                        "rp_group_id": lambda x: sorted(list(set(x))),
                        "software_description": "first",
                        "ai_description": "first",
                        "ai_core_features": "first",
                        "software_documentation": "first",
                        "ai_software_type": "first",
                        "ai_research_area": "first",
                        "ai_research_discipline": "first",
                        "ai_general_tags": "first",
                        "software_web_page": "first",
                        "ai_research_field": "first",
                        "software_use_link": "first",
                        "rp_software_documentation": lambda software_documentation: self.format_software_info(
                            df, software_documentation
                        ),
                        "software_versions": lambda software_versions: self.format_software_info(
                            df, software_versions
                        ),
                        "ai_software_class": "first",
                        "ai_example_use": "first",
                    }
                )
                .reset_index(drop=True)
            )

            # Handle include/exclude columns
            if include_columns:
                essential_columns = (
                    {"software_name"} if software_names else {"rp_name", "rp_group_id"}
                )
                include_columns = include_columns.union(essential_columns)
                df = df[list(include_columns.intersection(df.columns))]

            if exclude_columns:
                df = df.drop(
                    columns=[col for col in exclude_columns if col in df.columns],
                    errors="ignore",
                )
            # Ensure specific column order after inclusion/exclusion
            desired_column_order = [
                "software_name",
                "rp_name",
                "rp_group_id",
                "software_description",
                "ai_description",
                "ai_core_features",
                "software_documentation",
                "ai_software_type",
                "ai_research_area",
                "ai_research_discipline",
                "ai_general_tags",
                "software_web_page",
                "ai_research_field",
                "software_use_link",
                "rp_software_documentation",
                "software_versions",
                "ai_software_class",
                "ai_example_use",
            ]

            # Reorder columns if possible, after handling include/exclude
            df = df[[col for col in desired_column_order if col in df.columns]]

            # Return as CSV or JSON
            match response_type:
                case "csv":
                    return Response(df.to_csv(index=False), mimetype="text/csv")
                case "json":
                    return jsonify(df.to_dict(orient="records"))
                case "html":
                    return Response(df.to_html(index=False), mimetype="text/html")

        except Exception as e:
            print(e)
            return make_response(({"message": "Invalid request parameters"}), 404)

        finally:
            logger.info("Closing connection to DB.")
            # Close the database connection manually if needed
            if not view_db.is_closed():
                view_db.close()

    def format_software_info(self, df: pd.DataFrame, x: pd.Series) -> list[str]:
        """Formats and groups software documentation or version information
        with with its respective rp name.

        Formats and groups together rp_software_documentation or
        software_versions entries for JSON output by combining the RP name with
        the respective documentation or version info. Uses the original
        DataFrame to retrieve RP names based on the index of the current Series
        being aggregated.

        Args:
            df (pd.DataFrame): Original DataFrame containing all software
                and RP data.
            x (pd.Series): Current Series being processed during aggregation,
                contains either 'rp_software_documentation' or
                'software_versions'.

        Returns:
            list[str]: List of strings where each entry is in the format
                'rp_name: info', combining RP names with their respective
                software documentation or versions.

        Example:
        >>> df = pd.DataFrame({'rp_name': ['A', 'B'], 'other_col': [1, 2]})
        >>> x = pd.Series(['documentation1', 'documentation2'], index=[0, 1])
        >>> format_software_info(df, x)
        ['A: documentation1', 'B: documentation2']
        """
        return sorted(list(set(
            f"{rp_name}: {info}"
            # df.loc[x.index, 'rp_name'] Retrieves the rp_name values
            #  corresponding to the indices in x from df
            for rp_name, info in zip(df.loc[x.index, "rp_name"], x)
        )))

    @db_operation("view")
    def load_tables(self) -> pd.DataFrame:
        """Gets all available data for all software

        Performs a join on RPSoftware, Software, RPS, and AISoftwareInfo
        tables to obtain all avaialble data. An inner join is used for all
        tables except AISoftwareInfo which is joined using a left outer join

        Returns:
            pd.DataFrame: A pandas DataFrame with merged data from teh tables.
            Empty values are filled with an empty string ("")

        ## Notes
            Here are the index for the returned table:
            Index(['id', 'rp_id', 'software_id', 'software_versions',
            'rp_software_documentation',
            'rp_has_individual_software_documentation',
            'rp_software_module_type', 'software_name', 'software_description',
            'software_web_page', 'software_documentation', 'software_use_link',
            'rp_name', 'ai_description', 'ai_software_type',
            'ai_software_class', 'ai_research_field', 'ai_research_area',
            'ai_research_discipline','ai_core_features', 'ai_general_tags',
            'ai_example_use'], dtype='object')
        """
        logger.info('Loading table from DB.')
        with db.atomic():
            # Peewee join table query
            query = (
                RPSoftware.select(RPSoftware, Software, RPS, AISoftwareInfo)
                .join(Software, on=(RPSoftware.software_id == Software.id))
                .join(RPS, on=(RPSoftware.rp_id == RPS.id))
                .left_outer_join(
                    AISoftwareInfo, on=(AISoftwareInfo.software_id == Software.id)
                )
            )

            merged_df = pd.DataFrame(list(query.dicts()))

        merged_df.fillna("", inplace=True)
        return merged_df
