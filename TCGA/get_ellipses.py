import argparse
import json
import pandas

from .read_vectors import get_case_vector
from .constants import DOWNLOADS_FOLDER, ELLIPSES_FOLDER


def get_ellipses(cases=None):
    ELLIPSES_FOLDER.mkdir(parents=True, exist_ok=True)
    for case_folder in DOWNLOADS_FOLDER.glob('*'):
        case_name = case_folder.name
        if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
            ellipses = pandas.DataFrame([], columns=['x', 'y', 'width', 'height', 'orientation'])
            vector = get_case_vector(case_name=case_name)
            for roi_name, roi_group in list(vector.groupby('roiname')):
                components = roi_name.split('_')[2:]
                roi = {}
                for component in components:
                    key, value = component.split('-')
                    roi[key] = int(value)
                for index, row in roi_group.iterrows():
                    ellipses.loc[len(ellipses)] = dict(
                        x=row["Unconstrained.Identifier.CentroidX"] * 2 + roi.get('left'),
                        y=row["Unconstrained.Identifier.CentroidY"] * 2 + roi.get('top'),
                        width=row["Size.MinorAxisLength"] * 2,
                        height=row["Size.MajorAxisLength"] * 2,
                        orientation=0 - row["Orientation.Orientation"],
                    )
            with open(ELLIPSES_FOLDER / f'{case_name}.json', 'w') as f:
                contents = ellipses.to_dict(orient='records')
                json.dump(contents, f)
                print(f'Wrote {len(ellipses)} ellipses to {f.name}.')


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        prog="ExampleDataLoader",
        description="Transfer data from example server to target server.",
    )
    parser.add_argument(
        '--cases', nargs='*',
        help='List of case names to process. If not specified, process all non-test cases.'
    )
    args = vars(parser.parse_args(raw_args))
    get_ellipses(args.get('cases'))


if __name__ == '__main__':
    main()
