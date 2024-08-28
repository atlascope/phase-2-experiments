import pandas
import json
from pathlib import Path
from typing import Optional

from .constants import CONF


def write_annotation(
    filepath: Path,
    vector: pandas.DataFrame,
    meta_vector: Optional[pandas.DataFrame],
):
    features = []
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)

    # assumes roiname is a string like "TCGA-3C-AALI-01Z-00-DX1_roi-0_left-15953_top-45779_right-18001_bottom-47827"
    for roi_name, roi_group in vector.groupby('roiname'):
        components = roi_name.split('_')[2:]
        region = {}
        for component in components:
            key, value = component.split('-')
            region[key] = int(value)
        roi_center = [
            (region.get('right') + region.get('left')) / 2,
            (region.get('bottom') + region.get('top')) / 2,
        ]
        for index, feature in roi_group.iterrows():
            major, minor, centroidX, centroidY, orientation = [
                feature['Size.MajorAxisLength'],
                feature['Size.MinorAxisLength'],
                feature['Unconstrained.Identifier.CentroidX'],
                feature['Unconstrained.Identifier.CentroidY'],
                feature['Orientation.Orientation'],
            ]
            # coordinates are relative to ROI and half resolution
            centroidX *= 2
            centroidY *= 2
            centroidX += region.get('left', 0)
            centroidY += region.get('top', 0)

            color = '#00FF00'
            meta = dict(
                id=feature['Identifier.ObjectCode']
            )
            if meta_vector is not None:
                meta.update(meta_vector.loc[index].to_dict())

            features.append(dict(
                type='ellipse',
                lineColor=color,
                lineWidth=2,
                fillColor=color,
                center=[centroidX, centroidY, 0],
                width=minor * 2,
                height=major * 2,
                rotation=(0 - orientation),  # negated orientation
                user=meta  # adhere to schema; user is unconstrained
            ))
    # export case_features to annotation file
    annotation = dict(
        name="TCGA Nuclei",
        description="Interpreted from feature vectors",
        display=dict(
            visible=True,
        ),
        elements=features
    )
    with open(filepath, 'w') as f:
        json.dump(annotation, f)


def upload_annotation(
    case_name: str,
    filepath: Path,
    username:str,
    password:str
):
    target_server = CONF.get('target_server', {})
    api_root = target_server.get('api_root')
    folder_id = target_server.get('folder_id')

    if not api_root or not folder_id:
        raise ValueError(
            "Configuration file must specify target_server.api_root and target_server.folder_id"
        )

    client = girder_client.GirderClient(apiUrl=api_root)
    client.authenticate(username, password)
    for item in client.listItem(folder_id, case_name):
        for old_annotation in client.get(
            'annotation',
            parameters=dict(itemId=item['_id']),
        ):
            old_id = old_annotation.get('_id')
            client.delete(
                f'annotation/{old_id}',
            )
        client.post(
            'annotation',
            parameters=dict(itemId=item['_id']),
            json=annotation_contents
        )
