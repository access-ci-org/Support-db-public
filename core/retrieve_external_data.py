import re
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import yaml
from jinja2 import Template, Undefined
from core.core_logging import logger
from core import custom_halo

logger.info("Fetching external software data from conda forge.")


class SafeUndefined(Undefined):
    """
    Custom Jinja2 Undefined handler that silently handles all undefined variables
    and functions during template rendering. Used when template should continue
    rendering even if variables are missing.

    Usage:
        template = Template(content, undefined=SafeUndefined).render()
    """

    def _fail_with_undefined_error(self, *args, **kwargs):
        return self

    def __str__(self):
        return ""

    def __bool__(self):
        return False

    def __call__(self, *args, **kwargs):
        return self

    def __add__(self, other):
        return ""

    def __format__(self, format_spec):
        return ""

    def __hash__(self):
        return 123

    __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = __truediv__ = __rtruediv__ = (
        __floordiv__
    ) = __rfloordiv__ = __mod__ = __rmod__ = __pos__ = __neg__ = __getitem__ = (
        __lt__
    ) = __le__ = __gt__ = __ge__ = __int__ = __float__ = __complex__ = __pow__ = (
        __rpow__
    ) = __sub__ = __rsub__ = __iter__ = __len__ = __nonzero__ = __eq__ = __ne__ = (
        _fail_with_undefined_error
    )


def get_software_info_from_conda_forge(software: str) -> dict[str, any]:
    """
    Fetches and parses metadata for a conda-forge package from its feedstock repository.

    Args:
        software (str): Name of the conda-forge package

    Returns:
        dict[str, any]: Dictionary containing package metadata with keys:
            - name: Package name
            - about: Package metadata from the about section
            - source: URL to package meta.yaml
            Returns {} if package not found or parsing fails

    Example:
        >>> info = get_conda_forge_software_info("numpy")
        >>> print(info["about"]["description"])
    """
    url = f"https://raw.githubusercontent.com/conda-forge/{software}-feedstock/main/recipe/meta.yaml"
    response = requests.get(url, timeout=5000)
    if response.status_code != 200:
        return {}
    content = response.content.decode("utf-8")

    try:
        template = Template(content, undefined=SafeUndefined).render()
    except TypeError as te:

        logger.debug(
            f"Non critical error while trying to convert jinja2 content for {software}.\
                  \n{te} \n skipping"
        )
        logger.debug(te)
        return {}

    # First try to get the about section
    pattern = r"^about:(.*?)(?=^[a-zA-Z].*:|\Z)"
    match = re.search(pattern, template, re.DOTALL | re.MULTILINE)

    if match:
        about_section = match.group(1)
        try:
            about_yaml = yaml.safe_load(f"about:{about_section}")["about"]
            if about_yaml:
                return {
                    "name": software,  # Use the original software name
                    "about": about_yaml,
                    "source": f"https://github.com/conda-forge/{software}-feedstock/blob/main/recipe/meta.yaml",
                }
            return {}

        except yaml.YAMLError as ye:
            logger.debug(
                f"Non critical yaml error when trying to parse {software}. \n Skipping"
            )
            logger.debug(ye)
            return {}


@custom_halo(text="Obtaining software info from conda forge")
def get_conda_forge_info(
    software: list,
    file: str = "data/conda_forge_softw_desc.json",
    max_workers: int = 10,
) -> dict[str, any]:
    """
    Retrieves or caches conda-forge package information for specified software packages.

    This function either loads cached package information from a JSON file or fetches it
    from conda-forge if the cache file doesn't exist. The information includes package
    metadata about description and source details.

    Args:
        software (list): List of software package names to retrieve information for.
        file (str, optional): Path to the JSON cache file. Defaults to
            "data/conda_forge_softw_desc.json".
        max_workers (int, optional): Number of max workers to run queries in parallel.

    Returns:
        dict[str, any]: A dictionary where:
            - Keys are software package names
            - Values are dictionaries containing:
                - "about": Package description and metadata
                - "source": Package source information

    Note:
        If the specified cache file doesn't exist, the function will:
        1. Fetch information for each package from conda-forge
        2. Create a new cache file with the fetched data
        3. Return the processed data

        If the cache file exists, it will load and return the cached data instead.
    """
    logger.info("Fetching external data for software from conda forge.")
    file_path = Path(file)
    if not file_path.exists():
        logger.info(f"File {file} not found. \n recreating")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            remote_software_data = list(
                executor.map(get_software_info_from_conda_forge, software)
            )
            remote_software_data = [result for result in remote_software_data if result]

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w+", encoding="utf-8") as f:
            json.dump(remote_software_data, f, indent=2)
    else:
        logger.info(f"File {file} already exists. Using conda forge data from it.")
        with open(file_path, "r", encoding="utf-8") as f:
            remote_software_data = json.load(f)

    remote_data = {
        software_datum["name"]: {
            "about": software_datum["about"],
            "source": software_datum["source"],
        }
        for software_datum in remote_software_data
    }

    return remote_data
