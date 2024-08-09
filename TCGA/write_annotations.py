import json
from datetime import datetime
from matplotlib.colors import to_hex

from .read_vectors import get_case_vector
from .TSNE.scikit import get_tsne_result
from .constants import (
    DOWNLOADS_FOLDER,
    ANNOTATIONS_FOLDER,
    ROIS,
    INCLUDE_TSNE,
    TSNE_NUM_COMPONENTS,
    TSNE_PERPLEXITY,
    COLOR_LABEL_KEY,
    COLORMAP,
)

print(f'Converting feature vectors to annotations...')
start = datetime.now()


for case in DOWNLOADS_FOLDER.glob('*'):
    case_features = []
    case_name = case.name.split('.')[0]
    print(f'\t{case_name}')
    vector = get_case_vector(case_name, rois=ROIS)

    tsne_result = None
    if INCLUDE_TSNE:
        tsne_result = get_tsne_result(
            case_name,
            ROIS,
            n_components=TSNE_NUM_COMPONENTS,
            perplexity=TSNE_PERPLEXITY,
            color_label_key=COLOR_LABEL_KEY,
            vector=vector.copy(),
        )

    # assumes roiname is a string like "TCGA-3C-AALI-01Z-00-DX1_roi-0_left-15953_top-45779_right-18001_bottom-47827"
    for roi_name, roi_group in vector.groupby('roiname'):
        if ROIS is not None and roi_name in ROIS:
            components = roi_name.replace(f'{case_name}_', '').split('_')
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
            for index, feature in roi_group.iterrows():
                major, minor, centroidX, centroidY, orientation = [
                    feature['Size.MajorAxisLength'],
                    feature['Size.MinorAxisLength'],
                    feature['Unconstrained.Identifier.CentroidX'],
                    feature['Unconstrained.Identifier.CentroidY'],
                    feature['Orientation.Orientation'],
                ]
                # Only multiply by 2 if getMetadata().getMagnification() is 40 (CSV data done at 20x)
                # coordinates are relative to ROI and half resolution
                centroidX *= 2
                centroidY *= 2
                centroidX += region.get('left', 0)
                centroidY += region.get('top', 0)

                color = '#00FF00'
                meta = dict(
                    id=feature['Identifier.ObjectCode']
                )
                if tsne_result is not None:
                    meta.update({f'tsne_{k}': v for k, v in tsne_result.iloc[index].to_dict().items()})
                    c = meta.get('tsne_c')
                    if c is not None:
                        color = to_hex(COLORMAP.colors[int(c)])

                case_features.append(dict(
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
        elements=case_features
    )
    with open(ANNOTATIONS_FOLDER / f'{case_name}.json', 'w') as f:
        json.dump(annotation, f)

print(f'Completed conversion in {datetime.now() - start} seconds.')
