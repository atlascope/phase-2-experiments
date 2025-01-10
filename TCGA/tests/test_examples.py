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
        'Generating parquet file of vector data...',
        'Reading features in 3 region\(s\).',
        'Found 3586 features.',
        'Uploading image and parquet file for test.',
        'Completed upload in ([\d:.]*) seconds.'
    ]
    compare_outputs(output, expected_output)
