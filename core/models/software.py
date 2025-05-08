from . import *

class Software(BaseExtModel):
    id = PrimaryKeyField()
    software_name = CaseInsensitiveField(unique=True)
    software_description = TextField()
    software_web_page = CharField()     # Link to the software's main webpage
    software_documentation = CharField()    # Link to the software's main documentation page
    software_use_link = TextField()   # Link to examples of software being used