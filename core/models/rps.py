from . import *

class RPS(BaseExtModel):
    id = PrimaryKeyField()
    rp_name = CaseInsensitiveField(null=False)
    rp_group_id = CaseInsensitiveField(null=False)
    rp_resource_id = CaseInsensitiveField(unique=True, null=False)

