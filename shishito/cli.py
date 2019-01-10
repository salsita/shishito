# -*- coding: utf-8 -*-

"""Console script for shishito."""
import sys
import click
from shishito.shishito_runner import ShishitoRunner
import os


@click.command()
def main(args=None):
    """Console script for pyforecast."""
    click.echo("This is Shishito test runner")
    click.echo("See click documentation at http://click.pocoo.org/")
    ShishitoRunner(os.getcwd()).run_tests()


if __name__ == "__main__":
    sys.exit(main())