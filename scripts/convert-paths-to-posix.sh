#!/bin/bash
# Convert Windows paths to POSIX format in tool outputs
# Usage: cat tool_output.json | convert-paths-to-posix.sh
# Converts: C:\Users\... → /c/Users/...
#           backslashes → forward slashes

perl -pe 's|C:\\\\|/c/|g; s|\\\\|/|g'
