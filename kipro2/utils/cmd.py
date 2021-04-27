import click
import shlex
import re
import logging
from typing import Set
import sys


# Define a custom command class which reads arguments from the first line of the
# input program.
#
# See https://stackoverflow.com/a/46391887
class CommentArgsCommand(click.Command):
    def invoke(self, ctx):
        program_path = ctx.params["program"]
        if program_path is not None:
            with open(program_path, "r") as program_file:
                program_code = program_file.read()
                _read_args_from_code(ctx, program_code)

        return super(CommentArgsCommand, self).invoke(ctx)


def _click_sysargs(ctx: click.Context) -> Set[str]:
    """
    Return the set of args given via the command-line. This is necessary to
    distinguish default values from non-default values in click's Context. With
    the `ParameterSource` in the as of yet unreleased click 8.0 this would be
    unnecessary. Oh well.
    """
    args_parser = ctx.command.make_parser(ctx)
    args_values, _args_args, _args_order = args_parser.parse_args(sys.argv[1:])
    return set(args_values.keys())


def _read_args_from_code(ctx: click.Context, code: str):
    lines = code.splitlines()
    if len(lines) == 0:
        return
    match = re.fullmatch('(\\/\\/|#)\\s*ARGS:(.*\\-\\-(pre|post).*)', lines[0])
    if match is None:
        return
    args_str = match.group(2)
    args_parser = ctx.command.make_parser(ctx)

    try:
        args_values, _args_args, _args_order = args_parser.parse_args(
            shlex.split(args_str))
    except Exception as e:
        raise Exception(
            "exception occurred during parsing of description comment", e)
    sysargs = _click_sysargs(ctx)
    used_defaults = dict()
    for param, value in ctx.params.items():
        if param in args_values and param not in sysargs:
            ctx.params[param] = args_values[param]
            used_defaults[param] = args_values[param]
    logging.getLogger("kipro2").info(
        "using default arguments from file comments: %s", used_defaults)
