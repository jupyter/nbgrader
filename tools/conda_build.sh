#!/bin/bash -e

for version in 2.7 3.4 3.5; do
    # we need -c bokeh for the selenium package
    cmd="conda build --no-anaconda-upload --python $version -c bokeh conda.recipe"
    $cmd

    # the package gets built into some location we don't control, but we can
    # get the path by rerunning the command with --output
    out=$($cmd --output)
    conda convert --platform all $out -o conda-bld
done

for pkg in conda-bld/*/*.tar.bz2; do
    anaconda upload $pkg
done
