#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.verbose
'''

from argparse import ArgumentParser

verbose_parser = ArgumentParser(add_help=False)
verbose_parser.add_argument(
    '--verbose',
    metavar='LEVEL',
    dest='verbosity',
    default=0,
    const=1,
    type=int,
    nargs='?',
    help='set verbosity level')

