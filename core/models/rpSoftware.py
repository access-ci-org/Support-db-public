from core.models import *
from core.models.rps import RPS
from core.models.software import Software


class RPSoftware(BaseExtModel):
    id = PrimaryKeyField()
    rp_id = ForeignKeyField(RPS)
    software_id = ForeignKeyField(Software)
    software_versions = TextField()
    rp_software_documentation = TextField()
    rp_has_individual_software_documentation = BooleanField()

    # If rp classifies module as something other than software
    # mainly used to change rp url link for rps with individual software links
    # see createRPSoftwareTable.py for use
    rp_software_module_type = CharField(default="software")

    class Meta:
        # There should only be one row with a specific rp_id and software_id combination
        indexes = ((("rp_id", "software_id"), True),)
