"""
Software Name and Version Parser

This module parses software information from various ACCESS RPS,
normalizing names and versions to a consistent format.
"""

import re
import json
from collections import defaultdict
from pprint import pp
from typing import Callable, Any
from core.core_logging import logger

NAME_VERSION_PATTERN = re.compile(r"(.*?)-(\d.*?)") # spac specific items
NAME_VERSION_SPACE_PATTERN = re.compile(r"(.*?)\s(\d.*?)")

def clean_name_version(name: str, version: str) -> tuple[str, str]:
    """
    Apply common cleaning operations to software name and version.

    Args:
        name: Software name
        version: Software version

    Returns:
        Cleaned name and version
    """
    # Strip whitespace and convert to lowercase
    name = name.strip().lower() if name else ""
    version = version.strip().lower() if version else ""

    # Remove .lua extension
    name = name.replace(".lua", "")
    version = version.replace(".lua", "")

    # Convert undefined version to empty string
    if version == "undefined":
        version = ""

    # Skip null names
    if name in ["null"]:
        name = ""

    if name.startswith("."):
        name = name[1:]
    return name, version

def parse_name_with_version_pattern(name: str, version: str, pattern=NAME_VERSION_PATTERN) -> tuple[str, str]:
    """
    Parse name containing version information using a regex pattern.

    Args:
        name: Software name
        version: Software version
        pattern: Regex pattern to use for parsing

    Returns:
        Updated name and version
    """
    if version == "undefined" or not version:
        match = pattern.match(name)
        if match:
            new_name = match.group(1)
            version = match.group(2)
            name = new_name

    if " " in name and name.split()[1] == version:
        name = name.split()[0]

    return name, version

class SoftwareParser:
    """Parser for software name and version information."""

    def __init__(self):
        """Initialize the parser with rp-specific handlers."""
        self.rp_handlers = {
            "kyric": self.parse_kyric,
            "delta": self.parse_delta,
            "bridges": self.parse_bridges,
            "stampede": self.parse_stampede,
            "anvil": self.parse_anvil,
            "darwin": self.parse_darwin,
            "tamu": self.parse_tamu,
            "jetstream": self.parse_jetstream,
            "ookami": self.parse_ookami,
            "expanse": self.parse_expanse,
        }
        try:
            with open("data/software_blacklist", 'r', encoding='utf-8') as sb:
                self.blacklist = sb.readlines()
        except FileNotFoundError as fne:
            logger.warning(f"Error while trying find blacklist file: {fne}")
            self.blacklist = []

    def parse_delta(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse Delta software name and version format."""
        try:
            name = software_info["AppName"]
            version = software_info["AppVersion"]

            name, version = clean_name_version(name, version)

            # Handle special cases for craype modules
            if not version:
                if "craype-x86" in name:
                    version = name[len("craype-x86-"):]
                    name = "craype-x86"
                elif "craype-accel" in name:
                    version = name[len("craype-accel-"):]
                    name = "craype-accel"
                elif "craype" in name:
                    version = name[len("craype-"):]
                    name = "craype"

            # Handle cray modules
            elif "cray" in name:
                if name.startswith("cray-"):
                    name = name[len("cray-"):]
                elif name.endswith("-cray"):
                    name = name[:-len("-cray")]

            return name, version
        except Exception as e:
            print(f"Error parsing Delta software: {e}")
            return "", ""

    def parse_kyric(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse Kyric-specific software name and version format."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            # Handle cases where AppName sometimes contains sentences
            if "built" in name:
                name = name.split()[0]

            # Handle kyric containers
            elif "kyric" in name:
                name, version = version, ""

            elif name.startswith("oneapi/"):
                version = name.replace("oneapi/","")
                name = "oneapi"


            # Parse SPAC naming scheme for modules
            name, version = parse_name_with_version_pattern(name, version)

            return name, version
        except Exception as e:
            print(f"Error parsing Kyric software: {e}")
            return "", ""

    def parse_bridges(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software name and version information for Bridges."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            # Handle cases where version is in the name (e.g. "Pytorch 1.13.1")
            name, version = parse_name_with_version_pattern(name, version, NAME_VERSION_SPACE_PATTERN)

            # Skip anton3 modules
            if "anton3 minio client" in name:
                return "", ""

            return name, version
        except Exception as e:
            print(f"Error parsing Bridges software: {e}")
            return "", ""

    def parse_stampede(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for Stampede."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            if "tacc-" in name:
                name = name.replace("tacc-", "")

            return name, version
        except Exception as e:
            print(f"Error parsing Stampede software: {e}")
            return "", ""

    def parse_anvil(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for Anvil."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            if "intel® oneapi" in name:
                name = "oneapi"

            if "intel® mpi" in name:
                name = "impi"  # intel-mpi should be renamed to impi

            return name, version
        except Exception as e:
            print(f"Error parsing Anvil software: {e}")
            return "", ""

    def parse_darwin(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for Darwin."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            if version == "undefined":
                version = ""

            return name, version
        except Exception as e:
            print(f"Error parsing Darwin software: {e}")
            return "", ""

    def parse_tamu(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for TAMU. (faster and aces have same conventions)"""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            if name.startswith("xfce4"):
                version = name.replace("xfce4-", "") + "/" + version
                name = "xfce4"
            elif name.startswith("oneapi/"):
                version = name.replace("oneapi/","")
                name = "oneapi"


            return name, version
        except Exception as e:
            print(f"Error parsing TAMU software: {e}")
            return "", ""

    def parse_jetstream(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for Jetstream2."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            if name.startswith("nvhpc"):
                version = version + "/" + name.replace("nvhpc/", "")
                name = "nvhpc"

            return name, version
        except Exception as e:
            print(f"Error parsing Jetstream software: {e}")
            return "", ""

    def parse_ookami(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for Ookami."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            if name.startswith("nvidia"):
                name, version = self._handle_nvidia_name_version(name, version)

            elif name.startswith("hdf5/parallel"):
                name, version = self._handle_hdf5_parallel(name, version)

            elif "/" in name:
                split = name.split("/")
                version = "/".join(split[1:]) + "/" + version
                name = split[0]

            name, version = clean_name_version(name, version)

            return name, version
        except Exception as e:
            print(f"Error parsing Ookami software: {e}")
            return "", ""

    def _handle_nvidia_name_version(self, name: str, version: str) -> tuple[str, str]:
        """Handle NVIDIA-specific naming conventions on ookami."""
        split = name.split("/")
        if len(split) == 1:
            # Special case where version has the actual software name
            match = NAME_VERSION_PATTERN.match(version)
            if match:
                new_name = match.group(1)
                version = version.replace(f"{new_name}", "")
                name = new_name
        else:
            name = split[-1]
            if len(split) > 2:
                version = version + "/" + split[1]

        return name, version

    def _handle_hdf5_parallel(self, name: str, version: str) -> tuple[str, str]:
        """Handle HDF5 parallel naming conventions on ookami."""
        if "openmpi" in name:
            version = name + "/" + version
            name = "openmpi"
        elif "mvapich2" in name:
            split = name.replace("hdf5/parallel", "").split("/")
            version = name + "/" + version
            if split and split[-1][-1].isdigit():
                name = split[-2] if len(split) > 1 else "mvapich2"
            else:
                name = split[-1] if split else "mvapich2"

        return name, version

    def parse_expanse(self, software_info: dict[str, str]) -> tuple[str, str]:
        """Parse software information for Expanse."""
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            return name, version
        except Exception as e:
            print(f"Error parsing Expanse software: {e}")
            return "", ""

    def parse_generic(self, software_info: dict[str, str]) -> tuple[str, str]:
        """
        Parse software information for RPs that don't need a custom parser for or
        we don't have one yet.
        """
        try:
            name = software_info['AppName']
            version = software_info['AppVersion']

            name, version = clean_name_version(name, version)

            return name, version
        except Exception as e:
            print(f"Error parsing generic software: {e}")
            return "", ""

    def get_parser_for_rp(self, rp_id: str) -> Callable:
        """
        Get the appropriate parsing function for the given rp.

        Args:
            rp_id: Resource provider id.

        Returns:
            Parsing function for the rp.
        """
        for rp, handler in self.rp_handlers.items():
            if rp in rp_id:
                return handler

        return self.parse_generic

    def parse_software(self, rp_software: dict[dict[str, str]], rp_id: str) -> dict[str, set[str]]:
        """
        Parse software information for the given rp.

        Args:
            rp_software: List of software information dictionaries.
            rp_id: Resource provider identifier.

        Returns:
            Dictionary mapping software names to sets of versions.
        """
        software = defaultdict(set)
        parse_func = self.get_parser_for_rp(rp_id)

        for software_info in rp_software:
            if software_info.get('AppName') and software_info['AppName'] != "null":
                try:
                    name, version = parse_func(software_info)
                    if name and not name in self.blacklist:
                        software[name].add(version)
                except Exception as e:
                    print(f"Error parsing software for {rp_id}: {e}")

        return software

def process_operations_data(filename: str, print_data: bool = False) -> dict[str, dict[str, Any]]:
    """
    Process operations data from a JSON file.

    Args:
        filename (str): Path to the operations data JSON file.
        print_data (bool): Print parsed data to console

    Returns:
        Dictionary mapping rp id to software information.
    """
    parser = SoftwareParser()
    results = {}

    try:
        with open(filename, 'r') as od:
            data = json.load(od)

        for key, item in data.items():
            software = parser.parse_software(item, key)
            results[key] = {
                **software
            }

            if print_data:
                # Print results
                pp(key)
                pp(software, sort_dicts=True)
                print(f"Total software count: {len(software)}")
                print("=" * 50)

        return results

    except FileNotFoundError:
        print(f"Error: {filename} file not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filename}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

    return {}

def save_results(results: dict[str, dict[str, Any]], output_file: str) -> None:
    """
    Save parsing results to a JSON file.

    Args:
        results: Dictionary of parsing results.
        output_file: Path to the output file.
    """
    try:
        # Convert sets to lists for JSON serialization
        serializable_results = {}
        for rp, software in results.items():
            software_dict = {}
            for name, versions in software.items():
                software_dict[name] = list(versions)

            serializable_results[rp] = {
                **software_dict,
                # "count": data["count"]
            }

        with open(output_file, "w") as f:
            json.dump(serializable_results, f, indent=2)

        print(f"Results saved to {output_file}")

    except Exception as e:
        print(f"Error saving results: {e}")

def parse_ipf_software(
        input_file: str = "data/operations_data.json",
        output_file: str = "data/parsed_software.json"
        ):
    """Main function to process operations data and save results."""

    results = process_operations_data(input_file)
    if results:
        save_results(results, output_file)

if __name__ == "__main__":
    parse_ipf_software()
