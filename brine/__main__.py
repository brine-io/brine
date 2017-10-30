import argparse
import sys

from brine.install import install
from brine.uninstall import uninstall
from brine.ls import ls
from brine.info import info
from brine.build import build
from brine.push import push
from brine.exceptions import BrineError


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='command', dest='command')
    subparsers.required = True

    # brine install <dataset>
    install_parser = subparsers.add_parser('install')
    install_parser.add_argument(
        'dataset',
        metavar='<dataset>',
        type=str)
    install_parser.set_defaults(func=lambda args: install(args.dataset))

    # brine uninstall <dataset>
    uninstall_parser = subparsers.add_parser('uninstall')
    uninstall_parser.add_argument(
        'dataset',
        metavar='<dataset>',
        type=str)
    uninstall_parser.set_defaults(func=lambda args: uninstall(args.dataset))

    # brine list
    ls_parser = subparsers.add_parser('list')
    ls_parser.set_defaults(func=lambda args: ls())

    # brine info <dataset>
    info_parser = subparsers.add_parser('info')
    info_parser.add_argument(
        'dataset',
        metavar='<dataset>',
        type=str)
    info_parser.set_defaults(func=lambda args: info(args.dataset))

    # brine build <dataset> --config=<config>
    build_parser = subparsers.add_parser('build')
    build_parser.add_argument(
        'dataset',
        metavar='<dataset>',
        type=str)
    build_parser.add_argument(
        '--config',
        metavar='<config>',
        required=True,
        type=str)
    build_parser.set_defaults(func=lambda args: build(args.dataset, args.config))

    # brine push <dataset>
    # push_parser = subparsers.add_parser('push')
    # push_parser.add_argument(
    #     'dataset',
    #     metavar='<dataset>',
    #     type=str)
    # push_parser.set_defaults(func=lambda args: push(args.dataset))

    args = parser.parse_args()

    try:
        args.func(args)
    except BrineError as ex:
        print('Error: %s' % str(ex), file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
