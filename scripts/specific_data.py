#!/usr/bin/env python3

"""Select specific data about elements and write them to a named file.

Use the --help for options and examples.

"""

import argparse
import csv
import json
import os
import sys
import textwrap
from collections import namedtuple
from pathlib import Path, PurePath


ColorCodes = namedtuple('ColorCodes', ['PURPLE', 'CYAN', 'DARKCYAN',
                                       'BLUE', 'GREEN', 'YELLOW',
                                       'RED', 'BOLD', 'UNDERLINE',
                                       'END',])

color_code = ColorCodes(PURPLE='\033[95m', CYAN='\033[96m', DARKCYAN='\033[36m',
                        BLUE='\033[94m', GREEN='\033[92m', YELLOW='\033[93m',
                        RED='\033[91m', BOLD='\033[1m', UNDERLINE='\033[4m',
                        END='\033[0m',)


# pylint: disable=missing-function-docstring
def pwclr(msg, color=color_code.RED):
    print(color + msg + color_code.END)


# pylint: disable=missing-function-docstring
def create_commandeline_parser(default_file):
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=textwrap.dedent(f"""
        examples:
          Properties written to a json file:
             $ {sys.argv[0]} --properties=name,atomic_mass --output name_mass.json

          Properties written to a csv file:
             $ {sys.argv[0]} --properties name,atomic_mass --output name_mass.csv

          Properties written into both files {default_file}.json and {default_file}.csv:
             $ {sys.argv[0]} --properties=name,atomic_mass

          Union of properties written into both files {default_file}.json and {default_file}.csv:
             $ {sys.argv[0]} --properties=name,atomic_mass --interactive

          Select properties interactively and write to files {default_file}.json and {default_file}.csv:
             $ {sys.argv[0]} --interactive

        NOTE: output files are written to the directory above {sys.argv[0]}.

        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    def comma_separated(arg):
        return arg.split(",")
    parser.add_argument('--properties', type=comma_separated, metavar='P1,...', nargs=1,
                        help='comma separated list of properties')

    parser.add_argument('--interactive', action="store_true",
                        help='whether to interactively select data')

    parser.add_argument('--output', metavar='FILENAME', nargs='?',
                        const=default_file, default=default_file,
                        help=f'where to output the data (default: {default_file}.{{json,csv}})')
    return parser


def read_periodic_table():
    """
    Load and return elements from the Periodic Table JSON file.

    This function reads the Periodic Table data from a JSON file located
    one directory above the current file's directory.

    Returns:
        tuple: A tuple containing two elements:
            - A list of dictionaries, where each dictionary represents an element
              with its properties as key-value pairs.
            - A set of strings, representing the keys (properties) available in
              the element dictionaries.
    """
    with open(os.path.join(Path(__file__).parents[1],'PeriodicTableJSON.json'),
              encoding="utf8") as file:
        elements = json.load(file)['elements']
    return elements, elements[0].keys()


def parse_properties(data_needed, args, keys):
    """
    Update data_needed with properties specified in args if they exist in keys.

    Parameters:
        data_needed (dict): A dictionary where each key represents a property name,
            and the value indicates whether the property is needed (True or False).
        args (argparse.Namespace): An object containing command line arguments.
            This function expects args to have a 'properties' attribute, which is
            a list of lists containing property names as strings.
        keys (list): A list of strings representing valid property names.

    Returns:
        dict: The updated data_needed dictionary with keys set to True for properties
           that are both requested in args and exist in keys.

    Side Effects:
        - Prints messages to the console indicating whether each requested property
          was found or not found.
        - Modifies the data_needed dictionary in-place by updating the values for
          keys that represent valid properties.
    """
    def show_bad(pval):
        message = ''.join([color_code.RED, 'Property ',
                           color_code.BLUE, pval,
                           color_code.RED, ' not found.',
                           color_code.END,])
        print(message)

    def show_good(pval):
        message = ''.join([color_code.GREEN, 'Property ',
                           color_code.BLUE, pval,
                           color_code.GREEN,' found.',
                           color_code.END,])
        print(message)

    props = set(args.properties[0])
    keys_as_set = set(keys)
    bad = props - keys_as_set
    good = props & keys_as_set
    data_needed.update({k:True for k in good})

    for pval in bad:
        show_bad(pval)
    for pval in good:
        show_good(pval)
    return data_needed


def parse_interactive(data_needed, keys):
    """
    Interactively update the data_needed dictionary based on user input.

    This function iterates over a list of keys, presenting each to the user
    and asking if it is needed. The user's response is used to update the
    data_needed dictionary: setting the value to True for keys that are needed.

    Parameters:
        data_needed (dict): A dictionary where each key represents a potential
            option, and the value (True/False) indicates whether it is needed.
        keys (list): A list of strings representing all possible options that
            the user can choose from.

    Returns:
        dict: The updated data_needed dictionary reflecting the user's choices.
            Keys corresponding to needed options are set to True.


    Note:
        The function calls an external 'clear()' function to clear the console
        before each iteration, improving readability of the interactive session.
    """
    def show_selected():
        message = ''.join([
            color_code.BOLD, color_code.GREEN,
            f'{len(data_needed)}', ' Option(s) Selected ',
            color_code.END,
            color_code.UNDERLINE, f'{list(data_needed.keys())}',
            color_code.END,
        ])
        print(message)

    def show_next():
        message = ''.join([
            'Do you need ',
            color_code.BOLD, color_code.BLUE, key, '? ',
            color_code.END,
        ])
        print(message)

    def default_input(prompt, default='y'):
        user_input = input(prompt)
        return user_input if  user_input else default

    def select_next():
        prompt = ''.join([
            color_code.GREEN, 'y/',
            color_code.RED, 'n/',
            color_code.BLUE, 'q(uit)',
            color_code.END, '[',
            color_code.PURPLE, 'default: ',
            color_code.GREEN, 'y',
            color_code.END, ']:',
        ])
        return default_input(prompt)

    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    clear()
    for key in keys:
        if key in data_needed:
            continue
        done = False
        while True:
            show_selected()
            show_next()
            needed = select_next()
            if needed == 'y':
                data_needed[key] = True
                break
            if needed == 'n':
                break
            if needed == 'q':
                done = True
                break
            print('Invalid input')
            continue
        if done:
            break
        clear()
    return data_needed


def save2file(args, elements, data_needed, default_file):
    """Filter data from `elements` based on `data_needed`. Save to file `args.output`.

    The function supports saving in JSON or CSV format. If
    `args.output` equals `default_file`, it saves in both formats
    using `default_file` as the base name. Otherwise, it saves in the
    format specified in `args.output`. Only .json and .csv extensions
    are supported.

    Parameters
    ----------
    args : argparse.Namespace
        Contains 'output' attribute specifying the output filename or path.
    elements : list of dicts
        Data to be filtered and saved.
    data_needed : dict
        Specifies keys to include from `elements`.
    default_file : str
        Default filename if `args.output` is not specified or matches `default_file`.

    Raises
    ------
    ValueError
        If `args.output` has an unsupported file extension (.json or .csv only).

    """
    def selected_from(elements, data_needed):
        data  = [{k: each[k] for k in data_needed} for each in elements]
        header = data_needed.keys()
        return data, header

    data, header = selected_from(elements, data_needed)

    # Command line with --output or just --output
    if args.output == default_file:
        write_json(default_file + '.json', data)
        write_csv(default_file + '.csv', data, header)
        return

    # Command line with --output FILENAME
    filename = args.output
    if not filename.endswith(('.json', '.JSON', '.csv', '.CSV')):
        raise ValueError("Unsupported file extension. Enter a .json or .csv file.")

    if filename.lower().endswith('.json'):
        write_json(filename, data)
    if filename.lower().endswith('.csv'):
        write_csv(filename, data, header)


def write_csv(output, data, header):
    """Writes data to a CSV file with the specified header.

    The file is saved in the parent directory of the script's
    location.

    Parameters:

        output (str): The base name for the output CSV file.

        data (list of dict): A list of dictionaries containing the
        data to be written.

        header (list of str): A list of strings representing the
        column headers for the CSV file.

    """
    fname = os.path.join(Path(__file__).parents[1], PurePath(output).name)
    with open(fname, 'w', newline='', encoding="utf8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)


def write_json(output, data):
    """Writes data to a JSON file at a specified output path.

    The file is saved in the parent directory of the script's location.

    Parameters:
        output (str): The base name for the output JSON file. The
        '.json' extension should be included in the name.

        data: The data to be serialized into JSON. Can be any data
        type that is supported by the json.dump() function.

    """
    fname = os.path.join(Path(__file__).parents[1], PurePath(output).name)
    with open(fname, 'w', encoding="utf8") as jsonfile:
        json.dump(data, jsonfile, indent=4)


# pylint: disable=missing-function-docstring
def main():
    def validate(args):
        # Command line with no --output or just --output
        if args.output == default_file:
            pass
        elif not args.output.endswith(('.json', '.JSON', '.csv', '.CSV')):
            raise ValueError("Unsupported file extension. Enter a .json or .csv file.")

    default_file = 'SpecificData'
    parser = create_commandeline_parser(default_file)
    args = parser.parse_args()
    validate(args)

    elements, keys = read_periodic_table()

    data_needed = {}
    if args.properties:
        data_needed = parse_properties(data_needed, args, keys)
    if args.interactive:
        data_needed = parse_interactive(data_needed, keys)
    if data_needed:
        save2file(args, elements, data_needed, default_file)
    else:
        pwclr("No properties selected.")


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except ValueError as err:
        pwclr(f"ERROR: {err}")
        sys.exit(1)
