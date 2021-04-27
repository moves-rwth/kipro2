#!/bin/bash
echo "Running: poetry run kipro2_benchmark run $@"
echo ""

poetry run kipro2_benchmark run $@
