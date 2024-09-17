# Atlascope Phase II experiments
Various experimental scripts for Atlascope Phase II use cases

## Getting Started

### Run prototype application

1. Run `cd atlascope_prototype`

2. Run `cd client && npm i && cd ..`

3. Run `docker compose up`

4. While the docker containers are running, in another terminal, run `docker compose exec girder python3 init.py` and supply a username and password for your admin user.

5. Similarly while the containers are running, run `docker compose exec server python3 -m server.populate` and supply the same username and password to authenticate the population script. This will download examples from the example server, upload them to your local Girder instance, and make records for these images and their feature vectors in Atlascope. This will take some time for all example cases; you can narrow the set of example cases to load by specifying `--cases [case_names]`.

6. Navigate to `localhost:3000` in your browser. You have an instance of [Girder](https://girder.readthedocs.io) running.

7. Navigate to `localhost:8080` in your browser. This is the Atlascope web client.

### Run TCGA Examples

1. (Optional) Update the values in `conf.json` if you made any changes to the docker compose configuration.

2. Install Python requirements for TCGA scripts: `pip install -r requirements.txt`

3. Download example data (this may take up to 90 minutes)

    python -m TCGA.examples download

4. Process feature vectors

    python -m TCGA.process_feature_vectors

    **Note:** The above command takes many arguments for custom processing. Use ``python -m TCGA.process_feature_vectors -h`` to read the help menu, or refer to the example usages shown below.

### Process Feature Vectors Example Commands

    python -m TCGA.process_feature_vectors --cases TCGA-3C-AALI-01Z-00-DX1 --rois TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971

    python -m TCGA.process_feature_vectors --reduce-dims --plot --groupby class

    python -m TCGA.process_feature_vectors --cases TCGA-3C-AALI-01Z-00-DX1 TCGA-3C-AALJ-01Z-00-DX1 --rois TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971 --reduce-dims --reduce-dims-func tsne --no-cache --plot --exclude-column-patterns slide roiname Unconstrained.Identifier.* Identifier.* SuperClassifProbab.* ClassifProbab.* Classif.* Unconstrained.Classif.* Unconstrained.SuperClassifProbab.* --groupby class --upload
