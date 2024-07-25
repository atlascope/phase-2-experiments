# Atlascope Phase II experiments
Various experimental scripts for Atlascope Phase II use cases


## Requirements
To view images and annotations, it is assumed that you have some instance of [Girder][girder-link] with Large Image installed where you can upload items. Upload scripts will require authentication to this server.

Update the following values in `conf.json`:

 - `target_server.api_root`: Girder URL like "https://data.kitware.com/api/v1/"
 - `target_server.folder_id`: ID of a folder where you have write access

Any additional requirements can be installed with the following command:

    pip install -r requirements.txt


## TCGA Example
1. Download example data (this may take up to 30 minutes)

    python TCGA/download_examples.py

2. Upload images to Girder

    python TCGA/upload_images.py

3. Create annotation file from feature vector data

    python TCGA/write_annotations.py

4. Upload annotations to Girder

    python TCGA/upload_annotations.py


[girder-link]: https://girder.readthedocs.io/
