from pathlib import Path
from utils import get_output, compare_outputs


def test_case_download():
    output = get_output(
        'python', '-m', 'TCGA.examples', 'download',
        '--cases', 'test',
    )
    expected_output = [
        'Downloading example data from https://data.kitware.com/api/v1/...',
        'Downloading test.',
        'Completed download in ([\d:.]*) seconds.',
    ]
    compare_outputs(output, expected_output)
    expected_filepath = Path('./TCGA/downloads/test/tcgaextract_rgb.tiff')
    assert expected_filepath.exists()


def test_case_upload():
    output = get_output(
        'python', '-m', 'TCGA.examples', 'upload',
        '--cases', 'test',
        '--username', 'admin',
        '--password', 'atlascope',
    )
    expected_output = [
        'Uploading examples...',
        'Uploading image for test.',
        'Reading features in 3 region\(s\).',
        'Found 3586 features.',
        'Generating parquet file of classification data...',
        'Uploading classification parquet file.',
        'Generating parquet file of unconstrained data...',
        'Uploading unconstrained parquet file.',
        'Generating parquet file of shape data...',
        'Uploading shape parquet file.',
        'Generating parquet file of nucleus data...',
        'Uploading nucleus parquet file.',
        'Generating parquet file of cytoplasm data...',
        'Uploading cytoplasm parquet file.',
        'Generating parquet file of basic data...',
        'Uploading basic parquet file.',
        'Completed upload in ([\d:.]*) seconds.'
    ]
    compare_outputs(output, expected_output)
