#!/usr/bin/env -S mako-render -s -a --
<%
import argparse
cli = argparse.ArgumentParser()
cli.add_argument("stuff")
cli.add_argument("--test")
args = cli.parse_args()
%>\
executable template ${args.stuff} ${args.test}