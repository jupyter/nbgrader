#!/usr/bin/env bash

set -ex


NODE_MAJOR_VERSION=`node --version | cut -d'.' -f 1 | cut -d'v' -f 2`

test_node_version () {
    MAJOR_VERSION_RE='^[0-9]+$'
    # checks if a version exists
    if ! [[ $1 =~ $MAJOR_VERSION_RE ]] ; then
        echo "Nodejs seems not installed. This requires nodejs>=14 to continue" >&2; exit 1
    fi
    # checks if the version is 14 or more
    if [ $1 -lt 14 ]; then
        echo "Nodejs version must be 14 or more, current is $1">&2; exit 1
    fi
}

test_node_version ${NODE_MAJOR_VERSION}

# Configuration variables.
root="$(realpath `dirname $0`)"
srv_root="/srv/nbgrader"
nbgrader_root="/srv/nbgrader/nbgrader"
jupyterhub_root="/srv/nbgrader/jupyterhub"
exchange_root="/usr/local/share/nbgrader/exchange"

# List of possible users, used across all demos.
possible_users=(
    'instructor1'
    'instructor2'
    'grader-course101'
    'grader-course123'
    'student1'
)

# Import helper functions.
source utils.sh

install_dependencies () {
    echo "Installing dependencies..."
    apt install -y npm
    npm install -g configurable-http-proxy
    apt install -y python3-pip
    pip3 install -U jupyterlab
    pip3 install -U jupyterhub
}

install_nbgrader () {
    local nbgrader_root="${1}"
    local exchange_root="${2}"

    echo "Installing nbgrader in '${nbgrader_root}'..."

    # Clone nbgrader.
    if [ ! -d "${nbgrader_root}" ]; then
        mkdir "${nbgrader_root}"
        cd "${nbgrader_root}"
        git clone https://github.com/jupyter/nbgrader .
    fi

    # Update git repository.
    cd "${nbgrader_root}"
    git pull

    # Install requirements and nbgrader.
    pip3 install -e ".[dev,docs,tests]"

    # Install global extensions, and disable them globally. We will re-enable
    # specific ones for different user accounts in each demo.
    jupyter labextension develop --overwrite .
    jupyter labextension disable --level=sys_prefix nbgrader:assignment-list
    jupyter labextension disable --level=sys_prefix nbgrader:formgrader
    jupyter labextension disable --level=sys_prefix nbgrader:course-list
    jupyter labextension disable --level=sys_prefix nbgrader:create-assignment
    jupyter server extension disable --sys-prefix --py nbgrader

    # Everybody gets the validate extension, however.
    jupyter labextension enable --level=sys_prefix nbgrader/validate_assignment
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.validate_assignment

    # Reset exchange.
    rm -rf "${exchange_root}"
    setup_directory "${exchange_root}" ugo+rwx

    # Remove global nbgrader configuration, if it exists.
    rm -f /etc/jupyter/nbgrader_config.py
}

restart_demo () {
    local demo="${1}"
    test ! -z "$demo"

    install_dependencies
    setup_directory "/etc/jupyter" ugo+r

    setup_directory "${srv_root}" ugo+r
    install_nbgrader "${nbgrader_root}" "${exchange_root}"

    # Delete existing user accounts.
    for user in ${possible_users[@]}; do
        remove_user "${user}"
    done

    # Setup the specific demo.
    echo "Setting up demo '${demo}'..."
    cd "${root}/${demo}"
    source setup_demo.sh
    setup_demo "${jupyterhub_root}"

    # Run JupyterHub.
    cd "${jupyterhub_root}"
    jupyterhub
}

restart_demo "${@}"