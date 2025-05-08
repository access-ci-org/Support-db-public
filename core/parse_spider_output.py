from typing import Callable, Dict, Any, Optional, List, Tuple
from pathlib import Path
import os
import re
from core.core_logging import logger
from core import custom_halo


def parse_delta_name_version(
    name: str, version: str, software_info: Dict
) -> Tuple[str, str, Dict]:
    """
    Parse Delta software name and version format.

    Args:
        name (str): Software name, potentially including additional info.
        version (str): Version string.
        software_info (Dict): Dictionary of known software.

    Returns:
        Tuple[str, str, Dict]: Processed name, version, and unchanged
            software_info.

    Note:
        Attempts to match name prefix with known software names.
    """
    if "/" not in version:
        software_names = [software["name"] for software in software_info]
        split_name = name.split("-")
        software_found = False

        for index in range(len(split_name) + 1):
            prefix = "-".join(split_name[:index])
            if prefix in software_names:
                software_found = True
                break
        if software_found:
            name = prefix
            version = version.replace(f"{name}-", "")
    if "/" in name:
        name = name.split("/", 1)[0]
    return name, version, software_info


def parse_kyric_name_version(
    name: str, version: str, software_info: str
) -> Tuple[str, str, Dict]:
    """
    Parse Kyric-specific software name and version format.

    Args:
        name (str): Software name, potentially including version info.
        version (str): Version string.
        software_info (str): Additional software information.

    Returns:
        Tuple[str, str, Dict]: Processed name, version, and unchanged
            software_info.

    Note:
        Handles cases where version info is embedded in the name.
    """
    if "/" not in version:
        pattern = r"(.*?)-(\d.*?)"
        match = re.match(pattern, name)
        if match:
            name = match.group(1)
            version = version.replace(f"{name}-", "")
    if "/" in name:
        name = name.split("/", 1)[-1]
    return name, version, software_info


def parse_bridges_name_version(
    name: str, version: str, software_info: Dict
) -> Tuple[str, str, Dict]:
    """
    Parse software name and version information for bridges, handling the 'AI'
        container case.

    Args:
        name (str): Software name. 'AI' triggers special processing.
        version (str): Version information.
        software_info (Dict): Existing software information.

    Returns:
        Tuple[str, str, Dict]: Processed name, version, and updated
            software_info.

    Note:
        Modifies software_info for 'AI' case, processing multiple packages.
    """
    if name == "AI":  # container with nested data
        software_version = [s_v.replace("AI/", "") for s_v in version.split(",")]
        software_and_versions = []
        for s_v in software_version:
            software_and_versions.append(s_v.split("_"))

        # leave one item since this function must return a software and version
        for s_v in range(len(software_and_versions) - 1):
            software, ver = software_and_versions[s_v]
            # Check if software already exists in software_info
            existing_software = next(
                (item for item in software_info if item["name"] == software), None
            )

            if existing_software:
                existing_software["versions"] = list(
                    set(existing_software["versions"] + ver)
                )
            else:
                software_info.append(
                    {
                        "name": software.strip().lower(),
                        "versions": ver.strip(),
                        "description": "",
                    }
                )
            software_and_versions.pop(s_v)

        name, version = software_and_versions[0]
    return name.strip(), version.strip(), software_info


def get_software_info(  # pylint: disable=too-many-positional-arguments,too-many-locals, too-many-arguments
    file_path: Path,
    section_separator: str = r"\n(?=\s{2}[/\w.+-]+(?:/[\w+\-])*:)",
    name_version_pattern: str = r"([/\w.+-]+(?:-[/\w+\-]+)?): (.+)",
    version_separator: str = r"[,]",
    version_cleaner: Callable[[str], str] = lambda v: v.split("/", 1)[-1],
    spider_description_separator: str = "----",
    custom_name_version_parser: Optional[Callable] = None,
    exclude_software: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract software information from a file.

    This function reads a file containing software information, parses it,
    and returns a list of dictionaries containing details about each software
    package.

    Args:
        file_path (Path): Path to the file containing software information.
        section_separator (str, optional): Regex pattern to split the file
            content into sections. A section is an entry of software name,
            versions, and descriptions (if availabe).
            Defaults to r'\\n(?=\\s{2}[\\/\\w.-]+(?:/[\\w-])*:)'.
        name_version_pattern (str, optional): Regex pattern to extract software
            name and version.
            Defaults to r'([\\w/.-]+(?:-[\\w/-]+)?): (.+)'.
        version_separator (str, optional): Regex pattern to split multiple
            versions.
            Defaults to r'[,]'.
        version_cleaner (Callable[[str], str], optional): Function to clean
            version strings.
            Defaults to lambda v: v.split('/',1)[-1].
        spider_description_separator (str, optional): Separator for spider
            descriptions.
            Defaults to '----'.
        custom_name_version_parser (Optional[Callable], optional): Custom
            function to parse
            name and version. If provided, it should return (name, versions,
            software_info).
            Defaults to None.
        exclude_software (List[str], optional): List of software names to
            exclude.
            Defaults to an empty list.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing:
            - 'name' (str): The name of the software.
            - 'versions' (List[str]): A list of versions for the software.
            - 'description' (str): A description of the software.

    Notes:
        - The function assumes the files are in the general spider output
            format, with each software entry starting with the software name and
            version(s), followed by a description.
        - If a software name already exists in the output list, the versions are
            merged and duplicates are removed.
        - The function removes LMOD comments from descriptions.
        - Software names in the `exclude_software` list are skipped.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    # Split the content into section (one for each software)
    sections = re.split(section_separator, file_content)
    software_info = []

    for section in sections:
        lines = section.strip().split("\n")
        if lines:
            # Extract software name and versions
            name_line = lines[0].strip()

            name_match = re.match(name_version_pattern, name_line)

            if name_match:
                if len(name_match.groups()) == 1:
                    name = name_match.group(1)
                    versions = ""
                else:
                    name, versions = name_match.groups()

                if custom_name_version_parser:
                    name, versions, software_info = custom_name_version_parser(
                        name, versions, software_info
                    )

                elif "/" in name:
                    name = name.split("/", 1)[0]
                versions = [
                    version_cleaner(v.strip())
                    for v in re.split(version_separator, versions)
                ]

                if exclude_software is not None and name.lower() in exclude_software:
                    # skip if software name should be excluded
                    continue

                # Join the remaining lines as the description
                description = " ".join(line.strip() for line in lines[1:])

                # remove lmod comments
                if spider_description_separator in description:
                    description = description.split(
                        spider_description_separator, maxsplit=1
                    )[0].strip()

                # Check if software already exists in software_info
                existing_software = next(
                    (item for item in software_info if item["name"] == name), None
                )

                if existing_software:
                    existing_software["versions"] = list(
                        set(existing_software["versions"] + versions)
                    )
                else:
                    software_info.append(
                        {
                            "name": name.lower(),
                            "versions": sorted(versions),
                            "description": description,
                        }
                    )
    return software_info


@custom_halo(text="Parsing Spider output")
def parse_spider_output(
    spider_output_dir: str = "./data/spiderOutput",
) -> Dict[str, List[Dict[str, Any]]]:
    """Parse the output of `module spider` and associate each rp with it's
    software, versions, and any given descriptions.

    Args:
        spider_output_dir (str): Relative path to the aprent directory
            containing all spider output files. Defaults to
            "./data/spiderOutput"

    Returns:
        Dict[str,List[Dict[str,Any]]]: A Dictionary with each key beign the rp
            name and the value is a list of Dicts with:
        - 'name' (str): The name of the software.
        - 'versions' (List[str]): A list of versions for the software.
        - 'description' (str): A description of the software.

    Behavior:
        - Iterates through files in the specified directory.
        - Extracts RP name from each filename.
        - Applies appropriate parsing logic based on the RP name.
        - Aggregates software and version information for each RP.

    Special cases:
        - delta: Uses custom parser, excludes 'default' software.
        - darwin: Uses custom section separator and name/version pattern,
            excludes 'Available' software.
        - kyric: Uses custom parser.
        - bridges2/bridges-2: Uses custom parser.
        - ookami: Excludes 'null' software.

    Example:
    >>> rp_data = parse_spider_output("/path/to/spider/output")
    >>> for rp, software_list in rp_data.items():
    >>>      print(f"RP: {rp}")
    >>>      for s_info in software_list:
    >>>          print(f"  Software: {s_info["name"]},
    >>>               Versions: {s_info["versions"]},
    >>>               Description: {s_info["description"]}")
    """
    rp_software_and_versions = {}

    for file in os.listdir(spider_output_dir):

        full_file_path = os.path.join(spider_output_dir, file)

        if not os.path.isfile(full_file_path):
            logger.info(
                f"Item {file} inside {spider_output_dir} is not a file. " + "Skipping"
            )
            continue

        rp_name = file.split("_")[0]  # Find the rp name from the file name
        if rp_name.lower() == "delta":
            exclude_software = ["default"]
            software_name_and_versions = get_software_info(
                full_file_path,
                custom_name_version_parser=parse_delta_name_version,
                exclude_software=exclude_software,
            )
        elif rp_name.lower() == "darwin":
            section_separator = r"\n(?=\s{4}[\/\w.-]+(?:/[\w-])*)"
            name_version_pattern = r"([\w-]+(?:-[\w/-]+)?)"
            exclude_software = ["Available"]
            software_name_and_versions = get_software_info(
                full_file_path,
                section_separator,
                name_version_pattern,
                exclude_software=exclude_software,
            )
        elif rp_name.lower() == "kyric":
            software_name_and_versions = get_software_info(
                full_file_path, custom_name_version_parser=parse_kyric_name_version
            )
        elif rp_name.lower() in ["bridges2", "bridges-2"]:
            software_name_and_versions = get_software_info(
                full_file_path, custom_name_version_parser=parse_bridges_name_version
            )
        elif rp_name.lower() == "ookami":
            exclude_software = ["null"]
            software_name_and_versions = get_software_info(
                full_file_path, exclude_software=exclude_software
            )
        elif rp_name.lower() == "expanse":
            exclude_software = ["defaultmodules", "default-environment"]
            software_name_and_versions = get_software_info(
                full_file_path, exclude_software=exclude_software
            )
        else:
            software_name_and_versions = get_software_info(full_file_path)

        rp_software_and_versions[rp_name] = []

        rp_software_and_versions[rp_name] += software_name_and_versions

    return rp_software_and_versions


if __name__ == "__main__":
    output = parse_spider_output()
    for key, value in output.items():
        print(f"{key}: {len(value)}")
    # print(sorted([item['name'].lower() for item in output['kyric']]))
