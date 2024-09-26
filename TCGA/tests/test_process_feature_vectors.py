import pytest
from utils import get_output, compare_outputs


BASE_COMMAND = ["python", "-m", "TCGA.process_feature_vectors"]


def test_help():
    output = get_output(*BASE_COMMAND, "-h")
    assert len(output) == 39
    assert output[0].startswith("usage:")


@pytest.mark.parametrize(
    "rois",
    [
        [
            "TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971",
            "TCGA-3C-AALI-01Z-00-DX1_roi-3_left-15953_top-53971_right-18001_bottom-56019",
        ],
        None,
    ],
)
def test_case_rois(rois):
    args = [
        "--cases",
        "test",
    ]
    if rois is not None:
        args += ["--rois", *rois]

    expected_n_regions = 3 if rois is None else 2
    expected_n_features = 3586 if rois is None else 2412
    expected_output = [
        "Evaluating test.",
        f"Reading features in {expected_n_regions} region\\(s\\).",
        f"Found {expected_n_features} features.",
        'Evaluating group "all".',
        "Done.",
    ]
    compare_outputs(get_output(*BASE_COMMAND, *args), expected_output)


@pytest.mark.parametrize("groupby", ["roi", "class", None])
def test_umap_groups(groupby):
    args = [
        "--cases",
        "test",
        "--rois",
        "TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971",
        "--reduce-dims",
        "--no-cache",
    ]
    if groupby is not None:
        args += ["--groupby", groupby]

    expected_output = [
        'Evaluating test.',
        'Reading features in 1 region\\(s\\).',
        'Found 1303 features.',
    ]
    expected_groups = [
        ('all', 1303)
    ]
    if groupby == 'roi':
        expected_groups = [
            ('TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971', 1303)
        ]
    elif groupby == 'class':
        expected_groups = [
            ('ActiveTILsCell', 1),
            ('CancerEpithelium', 632),
            ('NormalEpithelium', 3),
            ('StromalCellNOS', 535),
            ('TILsCell', 124),
            ('UnknownOrAmbiguousCell', 8)
        ]
    for group_name, feature_count in expected_groups:
        expected_output += [
            f'Evaluating group "{group_name}".',
            f'Evaluating UMAP for {feature_count} features... Completed in ([\d:.]*) seconds.',
        ]
    expected_output += [
        'Done.',
    ]
    compare_outputs(get_output(*BASE_COMMAND, *args), expected_output)


def test_tsne():
    args = [
        "--cases",
        "test",
        "--rois",
        "TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971",
        "--reduce-dims",
        "--no-cache",
        "--reduce-dims-func",
        "tsne",
    ]
    expected_output = [
        'Evaluating test.',
        'Reading features in 1 region\\(s\\).',
        'Found 1303 features.',
        'Evaluating group "all".',
        'Evaluating TSNE for 1303 features... Completed in ([\d:.]*) seconds.',
        'Done.'
    ]
    compare_outputs(get_output(*BASE_COMMAND, *args), expected_output)
