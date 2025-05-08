from . import *
from datetime import datetime

class API(BaseExtModel):
    id = PrimaryKeyField()
    organization = CharField()
    api_key = TextField(unique=True)
    can_edit = BooleanField(default=False)
    can_view = BooleanField(default=True)
    date_generated = DateField(default=datetime.now)
