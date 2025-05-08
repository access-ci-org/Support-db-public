import sys
import json
from . import Records
from core import custom_halo
from core.models import db_operation, db_proxy as db, use_db
from core.models.software import Software
from core.models.rps import RPS
from core.models.rpSoftware import RPSoftware
from core.db_logic.update_rp_table import update_rp_table
from core.core_logging import logger

parsed_ops_data = "./data/parsed_software.json"


# This logic works but rps don't have a dedicated page for all software so it gives dead
#   links most of the time
rp_with_individual_software_page = ["anvil", "bridges-2", "darwin"]

# Hard-coded links to RP-specific Software Documentation
# Key is rp_group_id
RP_URLS = {
    "aces.tamu.access-ci.org": "https://hprc.tamu.edu/software/aces",
    "anvil.purdue.access-ci.org": "https://www.rcac.purdue.edu/software",
    "bridges2.psc.access-ci.org": "https://www.psc.edu/resources/software",
    # "bridges2-cpu-ai.psc.access-ci.org": "https://www.psc.edu/resources/software",
    "darwin.udel.access-ci.org": "https://docs.hpc.udel.edu/software/",
    "delta-cpu.ncsa.access-ci.org": "https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/software.html",
    "delta-gpu.ncsa.access-ci.org": "https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/software.html",
    "expanse.sdsc.access-ci.org": "https://www.sdsc.edu/support/user_guides/expanse.html#modules",
    "faster.tamu.access-ci.org": "https://hprc.tamu.edu/software/faster",
    "jetstream2.indiana.access-ci.org": "",
    "kyric.uky.access-ci.org": "",
    "ookami.sbu.access-ci.org": "https://www.stonybrook.edu/commcms/ookami/support/faq/software_on_ookami",
    "stampede3.tacc.access-ci.org": "https://tacc.utexas.edu/use-tacc/software-list",
    "ranch.tacc.access-ci.org": "https://tacc.utexas.edu/use-tacc/software-list",
    "osg.access-ci.org": "",
    "osn.access-ci.org": "",
}

@custom_halo(text="Creating RP software table records")
def create_rp_software_table_records():
    """Creates records of data to be added to the RPSoftware table."""
    try:
        with open(parsed_ops_data, "r", encoding="utf-8") as file:
            software_data = json.load(file)
    except Exception as e:
        logger.error(f"Unable to read data from: {parsed_ops_data}")
        raise e

    rp_software_records = []
    # software_data = extract_software_data()

    if not software_data:
        # Skip if ResourceID is missing
        err_msg = f"Error: no data found in {parsed_ops_data}"
        logger.error(err_msg)
        print(err_msg)
        raise Exception(err_msg)

    for resource_id, software_info in software_data.items():
        software_name = software_info.get("resource_id")
        rp_modal = RPS.get_or_none(RPS.rp_resource_id == resource_id)
        rp_name = resource_id.split(".")[0].split("-")[0]

        if not rp_modal:
            # ResourceID is missing
            err_msg = f"Warning: ResourceID {resource_id} not found in database"
            logger.warning(err_msg)
            logger.info(f"Adding entry for resource_id: {resource_id}")

            # get rp_name (resource ids have this format: bridges2-gpu-ai.psc.access-ci.org)
            if "bridges" in rp_name:
                rp_name = "bridges-2"
            # get rp_group
            realted_rp_modal = RPS.get_or_none(RPS.rp_name == rp_name)

            if not realted_rp_modal:
                err_msg = f"""
                Unable to add entry for resource_id {resource_id}. No matching rp_name found
                """
                logger.error(err_msg)
                print(err_msg)
                continue
            rp_group = realted_rp_modal.rp_group_id

            rp_record = [
                {
                    "rp_name": rp_name,
                    "rp_group_id": rp_group,
                    "rp_resource_id": resource_id,
                }
            ]
            update_rp_table(rp_record)
            logger.info(f"Added new RP entry: {rp_record}")
            # obtain the newly created rp_modal
            rp_modal = RPS.get_or_none(RPS.rp_resource_id == resource_id)

        for software_name, versions in software_info.items():
            software_modal = Software.get_or_none(
                Software.software_name == software_name
            )
            versions = sorted(versions)  # sort version names
            if not software_modal:
                # Skip if ResourceID is missing
                err_msg = f"Warning: Software {resource_id} not found in database"
                # this warning should never not be raised since the same data is used to
                #  create an entry in the Software table
                logger.warning(err_msg)
                print(err_msg)
                continue

            url = RP_URLS.get(rp_modal.rp_group_id, "")
            # This logic works but rps don't have a dedicated page for all software so it gives dead
            #   links most of the time
            # if url and rp_name in rp_with_individual_software_page:
            #     url = f"{url}/{software_name}"

            # Map ResourceID to rp_name
            rp_software_records.append(
                {
                    "rp_id": rp_modal.id,
                    "software_id": software_modal.id,
                    "software_versions": ",".join(versions),
                    "rp_software_documentation": url,
                    "rp_has_individual_software_documentation": rp_modal.rp_name
                    in rp_with_individual_software_page,
                    # "rp_software_module_type": module_type,
                }
            )

    return rp_software_records


@custom_halo(text="Updating rp software table")
@db_operation("edit")
def update_rp_software_table(rp_software_records):
    """Adds or updates records in the RPSoftware table."""
    with db.atomic():
        for record in rp_software_records:
            try:
                RPSoftware.insert(**record).on_conflict(
                    conflict_target=[RPSoftware.software_id, RPSoftware.rp_id],
                    preserve=[
                        RPSoftware.software_versions,
                        RPSoftware.rp_id,
                        RPSoftware.rp_software_documentation,
                        RPSoftware.rp_has_individual_software_documentation,
                        RPSoftware.rp_software_module_type,
                    ],
                ).execute()
            except Exception as e:
                print(f"Error updating record {record}: {str(e)}")


if __name__ == "__main__":
    pass
