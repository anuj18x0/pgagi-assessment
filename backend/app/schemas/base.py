from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """
    Base schema for all models with strict validation.
    Explicitly disabling from_attributes (orm_mode) to follow user requirements.
    """
    model_config = ConfigDict(
        from_attributes=False,
        populate_by_name=True,
        str_strip_whitespace=True
    )
