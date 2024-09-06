from typing import Optional, Dict

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel, JSON


class ImageItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apiURL: str
    imageId: str = Field(sa_column=Column("imageId", String, unique=True))
    imageName: str
    levels: int
    magnification: Optional[float]
    mm_x: Optional[float]
    mm_y: Optional[float]
    sizeX: int
    sizeY: int
    tileWidth: int
    tileHeight: int


class Feature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    imageItemId: Optional[int] = Field(default=None, foreign_key="imageitem.id")
    index: int
    attrs: Dict = Field(default_factory=dict, sa_column=Column(JSON))
