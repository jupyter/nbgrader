#!/usr/bin/env bash

set -e

setup_directory () {
    local directory="${1}"
    local permissions="${2}"
    echo "Creating directory '${directory}' with permissions '${permissions}'"
    if [ ! -d "${directory}" ]; then
        mkdir -p "${directory}"
        if [[ ! -z "${permissions}" ]]; then
            chmod "${permissions}" "${directory}"
        fi
    fi
}

remove_user () {
    local user="${1}"
    echo "Removing user '${user}'"
    deluser "${user}" || true
    rm -rf "/home/${user}"
}

make_user () {
    local user="${1}"
    echo "Creating user '${user}'"
    useradd "${user}"
    yes "${user}" | passwd "${user}"
    mkdir "/home/${user}"
    chown "${user}:${user}" "/home/${user}"
}

setup_nbgrader () {
    USER="${1}"
    HOME="/home/${USER}"

    local config="${2}"
    local runas="sudo -u ${USER}"

    echo "Setting up nbgrader for user '${USER}'"

    ${runas} mkdir -p "${HOME}/.jupyter"
    ${runas} cp "${config}" "${HOME}/.jupyter/nbgrader_config.py"
    ${runas} chown "${USER}:${USER}" "${HOME}/.jupyter/nbgrader_config.py"
}

setup_jupyterhub () {
    local jupyterhub_root="${1}"

    echo "Setting up JupyterHub to run in '${jupyterhub_root}'"

    # Ensure JupyterHub directory exists.
    setup_directory ${jupyterhub_root}

    # Delete old files, if they are there.
    rm -f "${jupyterhub_root}/jupyterhub.sqlite"
    rm -f "${jupyterhub_root}/jupyterhub_cookie_secret"

    # Copy config file.
    cp jupyterhub_config.py "${jupyterhub_root}/jupyterhub_config.py"
}

enable_create_assignment () {
    USER="${1}"
    HOME="/home/${USER}"
    local runas="sudo -u ${USER}"

    ${runas} jupyter nbextension enable --user create_assignment/main
}

enable_formgrader () {
    USER="${1}"
    HOME="/home/${USER}"
    local runas="sudo -u ${USER}"

    ${runas} jupyter nbextension enable --user formgrader/main --section=tree
    ${runas} jupyter serverextension enable --user nbgrader.server_extensions.formgrader
}

enable_assignment_list () {
    USER="${1}"
    HOME="/home/${USER}"
    local runas="sudo -u ${USER}"

    ${runas} jupyter nbextension enable --user assignment_list/main --section=tree
    ${runas} jupyter serverextension enable --user nbgrader.server_extensions.assignment_list
}

enable_course_list () {
    USER="${1}"
    HOME="/home/${USER}"
    local runas="sudo -u ${USER}"

    ${runas} jupyter nbextension enable --user course_list/main --section=tree
    ${runas} jupyter serverextension enable --user nbgrader.server_extensions.course_list
}

create_course () {
    USER="${1}"
    HOME="/home/${USER}"
    local course="${2}"
    local runas="sudo -u ${USER}"
    local currdir="$(pwd)"

    cd "${HOME}"
    ${runas} nbgrader quickstart "${course}"
    cd "${course}"
    ${runas} nbgrader generate_assignment ps1
    ${runas} nbgrader release_assignment ps1
    cd "${currdir}"
}
