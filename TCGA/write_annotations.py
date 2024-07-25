import girder_client
import json
import math
import pandas
from pathlib import Path
from datetime import datetime


DOWNLOADS_FOLDER = Path(__file__).parent / 'downloads'
ANNOTATIONS_FOLDER = Path(__file__).parent / 'annotations'


with open('conf.json') as f:
    conf = json.load(f)


print(f'Converting feature vectors to annotations...')
start = datetime.now()


for case in DOWNLOADS_FOLDER.glob('*'):
    case_features = []
    case_name = case.name.split('.')[0]

    print(f'\t{case_name}')

    meta_vectors = case / 'nucleiMeta'
    prop_vectors = case / 'nucleiProps'

    meta_vector_files = list(meta_vectors.glob('*.csv'))
    prop_vector_files = list(prop_vectors.glob('*.csv'))

    print(f'\tReading features in {len(meta_vector_files)} regions.')

    if meta_vectors.exists() and prop_vectors.exists():
        for meta_vector_file in meta_vector_files:
            prop_vector_file = next((
                f for f in prop_vector_files
                if f.name == meta_vector_file.name
            ), None)
            if prop_vector_file:
                meta = pandas.read_csv(
                    str(meta_vector_file),
                    usecols=lambda x: 'Unnamed' not in x
                ).reset_index(drop=True)
                props = pandas.read_csv(
                    str(prop_vector_file),
                    usecols=lambda x: 'Unnamed' not in x
                ).reset_index(drop=True)
                intersection_cols = list(meta.columns.intersection(props.columns))
                # print(intersection_cols)
                props = props.drop(intersection_cols, axis=1)
                combo = pandas.concat([meta, props], axis=1)
                # print(meta.shape, props.shape, combo.shape)
                # print(list(combo.columns))

                # assumes roiname is a string like "TCGA-3C-AALI-01Z-00-DX1_roi-0_left-15953_top-45779_right-18001_bottom-47827"
                for roiname in combo['roiname'].mode():
                    components = roiname.replace(f'{case_name}_', '').split('_')
                    region = {}
                    for component in components:
                        key, value = component.split('-')
                        if key != 'roi':
                            region[key] = int(value)
                    # print(region)
                    roi_center = [
                        (region.get('right') + region.get('left')) / 2,
                        (region.get('bottom') + region.get('top')) / 2,
                    ]
                    case_features.append(dict(
                        type='rectangle',
                        lineColor='#FF0000',
                        lineWidth=2,
                        center=[*roi_center, 0],
                        width=(region.get('right') - region.get('left')),
                        height=(region.get('bottom') - region.get('top')),
                    ))
                    for index, feature in combo[combo['roiname'] == roiname].iterrows():
                        major, minor, centroidX, centroidY, orientation = [
                            feature['Size.MajorAxisLength'],
                            feature['Size.MinorAxisLength'],
                            feature['Identifier.CentroidX'],
                            feature['Identifier.CentroidY'],
                            feature['Orientation.Orientation'],
                        ]
                        # Only multiply by 2 if getMetadata().getMagnification() is 40 (CSV data done at 20x)
                        # coordinates are relative to ROI and half resolution
                        centroidX *= 2
                        centroidY *= 2
                        centroidX += region.get('left', 0)
                        centroidY += region.get('top', 0)
                        # case_features.append(dict(
                        #     type='point',
                        #     lineColor='#00FF00',
                        #     lineWidth=2,
                        #     center=[centroidX, centroidY, 0],
                        # ))
                        case_features.append(dict(
                            type='ellipse',
                            lineColor='#00FF00',
                            lineWidth=2,
                            center=[centroidX, centroidY, 0],
                            width=minor * 2,
                            height=major * 2,
                            rotation=(0 - orientation),  # negated orientation
                        ))
            else:
                print('No prop file for', meta_vector_file.name)
    else:
        print('No feature vector data found for', case_name)

    # export case_features to annotation file
    annotation = dict(
        name="TCGA Nuclei",
        description="Interpreted from feature vectors",
        display=dict(
            visible=True,
        ),
        elements=case_features
    )
    with open(ANNOTATIONS_FOLDER / f'{case_name}.json', 'w') as f:
        json.dump(annotation, f)

print(f'Completed conversion in {datetime.now() - start} seconds.')
