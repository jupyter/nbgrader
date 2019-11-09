#!/usr/bin/env bash

set -e

# Configuration variables.
root="/root"
srv_root="/srv/nbgrader"
nbgrader_root="/srv/nbgrader/nbgrader"
jupyterhub_root="/srv/nbgrader/jupyterhub"
exchange_root="/srv/nbgrader/exchange"

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
    pip3 install -U jupyter
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
    git checkout master
    git pull

    # Install requirements and nbgrader.
    pip3 install -U -r requirements.txt -e .

    # Install global extensions, and disable them globally. We will re-enable
    # specific ones for different user accounts in each demo.
    jupyter nbextension install --symlink --sys-prefix --py nbgrader --overwrite
    jupyter nbextension disable --sys-prefix --py nbgrader
    jupyter serverextension disable --sys-prefix --py nbgrader

    # Everybody gets the validate extension, however.
    jupyter nbextension enable --sys-prefix validate_assignment/main --section=notebook
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.validate_assignment

    # Reset exchange.
    rm -rf "${exchange_root}"
    setup_directory "${exchange_root}" ugo+rwx

    # Remove global nbgrader configuration, if it exists.
    rm -f /etc/jupyter/nbgrader_config.py
}

restart_demo () {
    local demo="${1}"

    install_dependencies
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
