#!/bin/bash
sed -i '' -r 's/^([0-9a-zA-Z_]+): (.+)$/    assert info.get("\1") == "\2"/g' test_e2e.py
