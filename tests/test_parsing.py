import pytest
from probably.pgcl.parser import parse_pgcl

from tests.sample_programs import *


def test_parsing_programs():
    for program in programs:
        parse_pgcl(program)
