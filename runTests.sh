#!/bin/bash

cd $(dirname $0)
PYTHONPATH=src python3 tests/testRecords.py
