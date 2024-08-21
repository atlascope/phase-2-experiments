# Atlascope Phase II experiments
Various experimental scripts for Atlascope Phase II use cases

<!-- TODO: update this -->
docker compose up
Girder -> Create User
Girder -> Create Assetstore (https://girder.readthedocs.io/en/latest/deployment.html#create-an-assetstore)


## Requirements
To view images and annotations, it is assumed that you have some instance of [Girder][girder-link] with Large Image installed where you can upload items. Upload scripts will require authentication to this server.

Update the following values in `conf.json`:

 - `target_server.api_root`: Girder URL like "https://data.kitware.com/api/v1/"
 - `target_server.folder_id`: ID of a folder where you have write access

Any additional requirements can be installed with the following command:

    pip install -r requirements.txt


## TCGA Example
1. Download example data (this may take up to 30 minutes)

    python -m  TCGA.download_examples

2. Upload images to Girder

    python -m TCGA.upload_images

3. Create annotation file from feature vector data

    python -m TCGA.write_annotations

4. Upload annotations to Girder

    python -m TCGA.upload_annotations

5. View TSNE Visualizations

    python -m TCGA.TSNE.display_tsne


[girder-link]: https://girder.readthedocs.io/
