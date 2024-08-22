# Atlascope Phase II experiments
Various experimental scripts for Atlascope Phase II use cases

## Getting Started

1. Run `docker compose up`
2. Navigate to `localhost:3000` in your browser. You have an instance of [Girder](https://girder.readthedocs.io) running.
3. Register a new Girder user. Since this is the first user created, this user will have admin privileges.
4. Configure your Girder instance. Sign in with your admin user and click on "Admin Console" in the sidebar.

    a. [Create an Assetstore](https://girder.readthedocs.io/en/latest/deployment.html#create-an-assetstore). In the Admin Console, click on "Assetstores", then click "Create New Filesystem Assetstore". Give it a name like "assets" and a root directory like "/assets". Since Girder is running in a Docker container, the root directory doesn't matter.

    b. [Update the CORS Policy](https://girder.readthedocs.io/en/latest/security.html#cors-cross-origin-resource-sharing). In the Admin Console, click "Server Configuration" and scroll to the bottom. Expand "Advanced Settings" and scroll to the CORS section. Enter "http://localhost:8080" for CORS Allowed Origins. This will allow the client application to fetch image tiles from this Girder instance.

5. (Optional) Update the values in `conf.json` if you made any changes to the docker compose configuration.
6. Install Python requirements for TCGA scripts: `pip install -r requirements.txt`

## TCGA Example
1. Download example data (this may take up to 90 minutes)

    python -m  TCGA.download_examples

2. Upload images to Girder

    python -m TCGA.upload_images

3. Create annotation file from feature vector data

    python -m TCGA.write_annotations

4. Upload annotations to Girder

    python -m TCGA.upload_annotations

5. View TSNE Visualizations

    python -m TCGA.TSNE.display_tsne
