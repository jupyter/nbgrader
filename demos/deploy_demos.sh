#!/usr/bin/env bash

set -e

server="${1}"
rsync -vrl --delete * "${server}":
