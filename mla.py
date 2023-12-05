import sys
import argparse
import src.todos
import src.inventory
import src.core


def main(arguments):
    debug = False
    dryrun = False
    parser = argparse.ArgumentParser(prog='mla',
                                     usage='%(prog)s [options] -f <FILE> -i <INVENTORY>',
                                     description='Command line program for configuration of remote hosts')

    parser.add_argument('-f', '--file', type=str, required=True)
    parser.add_argument('-i', '--inventory', type=str, required=True)
    parser.add_argument('--debug', action='store_true', help='Activate debug mode')
    parser.add_argument('--dry-run', action='store_true', help='Activate debug mode')

    args = parser.parse_args(arguments)

    # extracting config from the inventory and todos yaml and verify syntax of the file
    inventory_yaml = src.inventory.inventory(args.inventory)
    todos_yaml = src.todos.todos(args.file)

    if args.debug:
        debug = True

    if args.dry_run:
        debug = True

    src.core.core(inventory_yaml, todos_yaml, debug, dryrun)


if __name__ == '__main__':
    # what does at mean ?
    sys.exit(main(sys.argv[1:]))
