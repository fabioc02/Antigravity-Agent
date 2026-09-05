#!/bin/bash
set -e

DRIVE_ROOT=$(cd "$(dirname "$0")/.." && pwd)
"$DRIVE_ROOT/bin/agent" doctor
