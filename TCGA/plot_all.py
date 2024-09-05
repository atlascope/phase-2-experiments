import argparse

import matplotlib.pyplot as plt
import pandas

from .constants import REDUCE_DIMS_RESULTS_FOLDER
from .reduce_dims import plot_results


def plot_all(groupby):
    result_groups = {}
    for method_folder in REDUCE_DIMS_RESULTS_FOLDER.glob('*'):
        method_name = method_folder.name
        if method_name != 'plots':
            for case_folder in method_folder.glob('*'):
                case_name = case_folder.name
                for result_file in case_folder.glob('*'):
                    result = pandas.read_csv(result_file, index_col=0)
                    if groupby == 'case':
                        result_group_name = case_name
                        plot_name = result_file.name
                    elif groupby == 'class':
                        result_group_name = result_file.name
                        plot_name = case_name

                    if result_group_name not in result_groups:
                        result_groups[result_group_name] = {}
                    result_groups[result_group_name][plot_name] = result

    for group_name, group in result_groups.items():
        plot_results(group, title=group_name, show=False)
    plt.show()


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        prog="PlotResults",
        description="Plot all cached results of dimensionality reduction computations",
    )
    parser.add_argument(
        '--groupby', choices=['case', 'class'], default='case',
        help='Group plot results by this attribute. Default=case.'
    )
    args = vars(parser.parse_args(raw_args))
    groupby = args.get('groupby')
    plot_all(groupby)


if __name__ == '__main__':
    main()
