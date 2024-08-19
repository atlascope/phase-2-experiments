import girder_client
import pandas

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .services import engine, create_db_and_tables
from .models import ImageItem


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
            images = session.query(ImageItem.imageId, ImageItem.imageName).all()
            return [
                {"imageId": image_id, "imageName": image_name}
                for image_id, image_name in images
            ]

        except Exception as e:
            print(f"Failed to retrieve ImageItems: {e}")

@app.post("/images/")
async def add_image_item(imageItemData: ImageItem):
    imageId = imageItemData.imageId
    apiUrl = imageItemData.apiURL
    with Session(engine) as session:
        exist = session.query(ImageItem).filter(ImageItem.imageId == imageId).first()

        if not exist:
            gc = girder_client.GirderClient(apiUrl=apiUrl)
            try:
                itemInfo = gc.getItem(imageId)
                print(itemInfo)
                tileData = gc.get(f"item/{imageId}/tiles")
                imageItem = ImageItem(
                    imageName=itemInfo["name"],
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
