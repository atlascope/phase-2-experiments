from typing import Optional, List

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel, JSON
from pgvector.sqlalchemy import Vector


class ImageItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apiURL: str
    girderId: str = Field(sa_column=Column("imageId", String, unique=True))
    name: str

# JSON Implementation
# ingest took 66 seconds, fetch took 70 seconds
class FeatureVector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    imageItemId: Optional[int] = Field(default=None, foreign_key="imageitem.id", index=True)
    roiname: Optional[str] = Field(default=None)
    labels: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    features: List[List] = Field(default_factory=dict, sa_column=Column(JSON))


# Vector Implementation
# Vector fields are constrained by type, must be 1D and less than 16000 values
# One row per feature is a lot slower than one row per ROI
# ingest took 50 minutes, fetch took 2.5 minutes
# client keeps running out of memory
# class FeatureVector(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     index: Optional[int] = Field(default=None)
#     imageItemId: Optional[int] = Field(default=None, foreign_key="imageitem.id", index=True)
#     roiname: Optional[str] = Field(default=None)
#     labels: List[str] = Field(default_factory=list, sa_column=Column(JSON))
#     features: List[float] = Field(sa_column=Column(Vector()))
