# Atlascope Phase II experiments
Various experimental scripts and application prototypes for Atlascope Phase II use cases

## Run Prototype Application

1. Run `cd atlascope_prototype`
2. Run `docker compose up`
3. While the docker containers are running, in another terminal, run `docker compose exec girder python3 init.py` and supply a username and password for your admin user.
4. Navigate to [localhost:3000](localhost:3000) in your browser. You have an instance of [Girder](https://girder.readthedocs.io) running. You will need to update the CORS settings of your Girder instance.

    a. Click on "Log In" in the upper righthand corner and supply the username and password from Step 3.

    b. Click on "Admin Console" in the lefthand sidebar.

    c. Click on "Server Configuration", scroll down, and expand "Advanced Settings".

    d. Under the "CORS" section, type "*" in the field labeled "CORS Allowed Origins".

    e. Click the "Save" button at the very bottom of the page.

5. (**Optional**) Update the values in `conf.json` if you made any changes to the docker compose configuration.

## Get Example Data
For the following commands (excluding requirement installation), the default behavior is to evaluate all available example cases. Currently, there are ten example cases (and one test case) available on [data.kitware.com](https://data.kitware.com/#collection/66a14eba5d2551c516b1d5d6/folder/66a14ec45d2551c516b1d5d7).

Evaluating all ten cases can take a significant amount of time, so you can specify a subset of cases to the following TCGA commands to speed this up. For example, you can add `--cases TCGA-3C-AALI-01Z-00-DX1` to the end of these commands to only work with one example case or you can add `--cases TCGA-3C-AALI-01Z-00-DX1,TCGA-5L-AAT0-01Z-00-DX1,...` to the end of these commands to work with multiple example cases.

For additional convenience, the TCGA commands also accept `--username` and `--password` arguments for any procedures that involve uploading data to your Girder instance.

Run these commands in a new terminal.

1. Install Python requirements for TCGA scripts

    `pip install -r requirements.txt`

2. Download example data (this may take up to 90 minutes)

    `python -m TCGA.examples download`

3. Upload images to Atlascope

    `python -m TCGA.examples upload`

4. Compute dimensionality reduction and upload results

    `python -m TCGA.reduce_dims --upload`

    **Notes for reduce_dims:**
    - To view a scatterplot of the results, add `--plot` to this command.

    - By default, this command will use cached results if they exist. To avoid using cached results, add `--no-cache` to this command.

    - By default, this command uses UMAP dimensionality reduction. To use TSNE, add `--reduce-dims-func=tsne` to this command.

    - Some columns in the vector data may be irrelevant to dimensionality reduction. To exclude these columns, you can use the `--exclude-column-patterns` argument for this command. For example, `--exclude-column-patterns slide roiname Unconstrained.Identifier.* Identifier.*`


## Explore the data
Navigate to `localhost:8080` in your browser. This is the Atlascope web client.

Explore the data in your Girder instance using the data tree in the lefthand sidebar. Click on a case name to view the image, load the vector data, and visualize the detected nuclei in the image. The righthand sidebar will appear once the vector data is loaded. Use the options in this sidebar to explore the vector data.


<!-- Development Notes -->
<!-- Currently unused experiment files: process_feature_vectors, clustering, annotations -->
