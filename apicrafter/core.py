#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import logging
import click
import yaml


from .cmds.project import Project

# logging.getLogger().addHandler(logging.StreamHandler())
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


def enableVerbose():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG)


@click.group()
def cli1():
    pass

@cli1.command()
@click.option('--verbose', '-v', count=True, help='Verbose output. Print additional info on command execution')
def run(verbose):
    """Run server"""
    if verbose:
        enableVerbose()
    project = Project()
    project.run()
    pass

@click.group()
def cli2():
    pass

@cli2.command()
@click.option('--verbose', '-v', count=True, help='Verbose output. Print additional info on command execution')
def build(verbose):
    """Build API manifest"""
    if verbose:
        enableVerbose()
    project = Project()
    project.build()
    pass



@click.group()
def cli3():
    pass

@cli3.command()
@click.option('--verbose', '-v', count=True, help='Verbose output. Print additional info on command execution')
def init(verbose):
    """Init project dir"""
    if verbose:
        enableVerbose()
    project = Project(noload=True)
    project.init()
    pass


@click.group()
def cli5():
    pass


@cli5.command()
@click.option("--host", "-h", default="localhost", help="MongoDB host")
@click.option("--port", "-p", default=27017, help="MongoDB port")
@click.option("--dbname", "-d", default=None, help="Database name")
@click.option("--username", "-u", default=None, help="Username. Optional")
@click.option("--password", "-P", default=None, help="Password. Optional")
@click.option("--dbtype", "-y", default='mongodb', help="Database type")
def discover(
    host, port, dbname, username, password, dbtype
):
    """Build schema and project file from database"""
    acmd = Project(noload=True)
    acmd.discover(
        host,
        int(port),
        dbname,
        username,
        password,
        dbtype
    )


cli = click.CommandCollection(sources=[cli1, cli2, cli3, cli5])
