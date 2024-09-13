import pandas
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List

from .models import ImageItem, FeatureVector
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
            images = session.exec(select(
                ImageItem.id,
                ImageItem.girderId,
                ImageItem.name,
                ImageItem.apiURL,
            )).all()
            return [
                dict(
                    id=id,
                    girderId=girder_id,
                    name=name,
                    apiUrl=api_url,
                )
                for id, girder_id, name, api_url, in images
            ]

        except Exception as e:
            print(f"Failed to retrieve ImageItems: {e}")

@app.post("/images/")
async def add_image_item(imageItemData: ImageItem):
    girderId = imageItemData.girderId
    name = imageItemData.name
    apiUrl = imageItemData.apiURL
    with Session(engine) as session:
        exist = session.exec(select(ImageItem).filter(ImageItem.girderId == girderId)).first()
        if not exist:
            try:
                imageItem = ImageItem(
                    name=name,
                    apiURL=apiUrl,
                    girderId=girderId,
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

@app.get("/images/{imageItemId}/features/")
def get_image_features(imageItemId: int):
    with Session(engine) as session:
        image_vectors = session.exec(select(FeatureVector).filter(FeatureVector.imageItemId == imageItemId))

        # Vector Implementation
        # return [dict(
        #     id=v.id,
        #     index=v.index,
        #     roiname=v.roiname,
        #     labels=v.labels,
        #     features=v.features.tolist(),
        # ) for v in image_vectors]

        # JSON Implementation
        return [dict(
            id=v.id,
            roiname=v.roiname,
            labels=v.labels,
            features=v.features,
        ) for v in image_vectors]

@app.post("/images/{imageItemId}/features/")
def add_image_features(imageItemId: int, data: FeatureVector):
    with Session(engine) as session:
        features_vector = FeatureVector(
            imageItemId=imageItemId,
            roiname=data.roiname,
            labels=data.labels,
            features=data.features,
        )
        session.add(features_vector)
        session.commit()
        return features_vector
