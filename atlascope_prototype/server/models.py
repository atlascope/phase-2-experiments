from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field
from typing import Optional


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
