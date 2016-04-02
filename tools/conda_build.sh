#!/bin/bash -e

for version in 2.7 3.4 3.5; do
    cmd="conda build --no-anaconda-upload --python $version conda.recipe"
    $cmd
    out=$($cmd --output)
    conda convert --platform all $out -o conda-bld
done

for pkg in conda-bld/*/*.tar.bz2; do
    anaconda upload $pkg
done
