import girder_client
import pandas
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from typing import List

from .models import ImageItem, Feature
from .services import create_db_and_tables, engine

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# IMAGES

@app.get("/images/")
async def get_image_items():
    with Session(engine) as session:
        try:
            images = session.query(
                ImageItem.imageId,
                ImageItem.imageName,
                ImageItem.apiURL,
            ).all()
            return [
                dict(
                    id=id,
                    name=name,
                    apiUrl=api_url,
                )
                for id, name, api_url in images
            ]

        except Exception as e:
            print(f"Failed to retrieve ImageItems: {e}")

@app.post("/images/")
async def add_image_item(imageItemData: ImageItem):
    imageId = imageItemData.imageId
    imageName = imageItemData.imageName
    apiUrl = imageItemData.apiURL
    with Session(engine) as session:
        exist = session.query(ImageItem).filter(ImageItem.imageId == imageId).first()
        if not exist:
            gc = girder_client.GirderClient(apiUrl=apiUrl)
            try:
                tileData = gc.get(f"item/{imageId}/tiles")
                imageItem = ImageItem(
                    imageName=imageName,
                    apiURL=apiUrl,
                    imageId=imageId,
                    magnification=tileData["magnification"],
                    mm_x=tileData["mm_x"],
                    mm_y=tileData["mm_y"],
                    sizeX=tileData["sizeX"],
                    sizeY=tileData["sizeY"],
                    levels=tileData["levels"],
                    tileWidth=tileData["tileWidth"],
                    tileHeight=tileData["tileHeight"],
                )
                session.add(imageItem)
                session.commit()
                session.refresh(imageItem)
                return imageItem

            except Exception as e:
                print(f"Error while saving ImageItem: {e}")
        else:
            return exist

# FEATURES

@app.post("/images/{imageItemId}/features/")
def add_image_feature(imageItemId: int, featureDatas: List[Feature]):
    with Session(engine) as session:
        image_features = session.query(Feature).filter(Feature.imageItemId == imageItemId)
        for featureData in featureDatas:
            exist = image_features.filter(Feature.index == featureData.index).first()
            if not exist:
                try:
                    feature = Feature(
                        imageItemId=imageItemId,
                        index=featureData.index,
                        attrs=featureData.attrs,
                    )
                    session.add(feature)
                except Exception as e:
                    print(f"Error while saving Feature: {e}")
            else:
                exist.attrs = featureData.attrs
        session.commit()
        image_features = session.query(Feature).filter(Feature.imageItemId == imageItemId)
        return dict(
            imageItemId=imageItemId,
            featureIndices=[f.index for f in image_features]
        )
