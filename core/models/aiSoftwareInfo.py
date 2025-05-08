from . import *
from .software import Software

class AISoftwareInfo(BaseExtModel):
    id = PrimaryKeyField()
    software_id = ForeignKeyField(Software, unique=True)
    ai_description = TextField()
    ai_software_type = TextField()
    ai_software_class = TextField()
    ai_research_field = TextField()
    ai_research_area = TextField()
    ai_research_discipline = TextField()
    ai_core_features = TextField()
    ai_general_tags = TextField()
    ai_example_use = TextField()