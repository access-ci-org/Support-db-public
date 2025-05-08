from core.models import db_proxy as db, db_operation, use_db
from core.models.rpSoftware import RPSoftware
from core.models.software import Software
from core.models.rps import RPS
from core.models.aiSoftwareInfo import AISoftwareInfo
from core.models.api import API
from core.db_logic.update_rp_table import update_rp_table, create_rp_table_records
from core.db_logic.update_software_table import (
    update_software_table,
    create_software_table_records,
    update_software_records,
)
from core.db_logic.update_rp_software_table import (
    update_rp_software_table,
    create_rp_software_table_records,
)
from core.db_logic.update_ai_software_table import (
    create_ai_software_table_records,
    update_ai_software_table,
)
from core.db_logic.update_api_key_table import (
    create_api_key_table_records,
    update_api_key_table,
)

from core.get_operations_data import import_operations_data
from core.core_logging import logger
from core import custom_halo



@custom_halo(text="Recreating DB tables")
@db_operation("admin")
def recreate_tables():
    with db.atomic():
        main_tables = [RPS, Software, API]  # RPS with no foreign key fields
        dependant_tables = [RPSoftware, AISoftwareInfo]  # RPS with foreign key fields
        db.drop_tables(dependant_tables)
        db.drop_tables(main_tables)
        db.create_tables(main_tables + dependant_tables)


if __name__ == "__main__":
    logger.info("Resetting Database")

    recreate_tables()
    logger.info("Recreated DB tables")

    # data is saved to data/parsed_software.json
    import_operations_data()

    rp_table_records = create_rp_table_records()
    update_rp_table(rp_table_records)
    logger.info("RP table updated")

    # with use_db("view"):
    #     rps = RPS.select()
    # for rp in rps:
    #     print(rp.rp_name, rp.rp_group_id)

    # spider_output = parse_spider_output()

    # Write table info to file for testing purposes
    # with open("spider_output.txt", "w") as so:
    #     so.writelines(str(spider_output))

    columns = {
        "Software",
        "Software Description",
        "Software's Web Page",
        "Software Documentation",
        "Example Software Use",
    }
    software_table_records = create_software_table_records(columns)
    software_table_records = update_software_records(software_table_records)

    software_table_records = update_software_table(software_table_records)
    logger.info("Software table updated")

    # with open("sftw.txt", "w+") as s:
    #     for software in software_table_records:
    #         s.writelines(software["software_name"] + "\n")

    rp_software_records = create_rp_software_table_records()
    update_rp_software_table(rp_software_records)
    logger.info("RPSoftware table updated")

    # Write table info to file for testing purposes
    # with use_db("view"):
    #     rp_software = RPSoftware.select()
    # with open("rp_sftw_text.txt", "w") as rst:
    #     for rp_s in rp_software:
    #         rst.writelines(
    #             f"\nrp: {rp_s.rp_id.rp_name}, \
    #             software: {rp_s.software_id.software_name},\
    #             ver: {rp_s.software_versions}, type: {rp_s.rp_software_module_type},\
    #             doc: {rp_s.rp_software_documentation}, \
    #             has_solo_doc: {rp_s.rp_has_individual_software_documentation}"
    #         )

    columns = {
        "Software",
        "✨Research Area",
        "✨Example Use",
        "✨Software Class",
        "✨Research Field",
        "✨Core Features",
        "✨Research Discipline",
        "✨AI Description",
        "✨Software Type",
        "✨General Tags",
    }
    ai_software_records = create_ai_software_table_records(columns)
    update_ai_software_table(ai_software_records)
    logger.info("AISoftwareInfo table updated")

    # Write table info to file for testing purposes
    # with use_db("view"):
    #     ai_software = AISoftwareInfo.select()
    # with open("ai_sftw_text.txt", "w") as ast:
    #     for ai_s in ai_software:
    #         ast.writelines(
    #             f"\nsoftware: {ai_s.software_id.software_name}, \
    #                 desc: {ai_s.ai_description}, \
    #                 s_type: {ai_s.ai_software_type}, s_class: {ai_s.ai_software_class},\
    #                 r_field: {ai_s.ai_research_field}, \
    #                 r_area: {ai_s.ai_research_area}, \
    #                 r_discipline: {ai_s.ai_research_discipline},\
    #                 c_features: {ai_s.ai_core_features}, g_tags: {ai_s.ai_general_tags},\
    #                 e_use: {ai_s.ai_example_use}"
    #         )

    api_key_records = create_api_key_table_records()
    update_api_key_table(api_key_records)
    logger.info("API table updated")
