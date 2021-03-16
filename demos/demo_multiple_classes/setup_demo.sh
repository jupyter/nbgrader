#!/usr/bin/env bash

set -e

get_token () {
    local jupyterhub_root="${1}"
    local user="${2}"
    local currdir="$(pwd)"
    cd "${jupyterhub_root}"
    local token=$(jupyterhub token "${2}")
    cd "${currdir}"
    echo "$token"
}

setup_demo () {
    # Setup JupyterHub config.
    local jupyterhub_root="${1}"
    setup_jupyterhub "${jupyterhub_root}"

    # Create users.
    make_user instructor1
    make_user instructor2
    make_user grader-course101
    make_user grader-course123
    make_user student1

    # Install global nbgrader config file.
    mkdir -p /etc/jupyter/
    cp global_nbgrader_config.py /etc/jupyter/nbgrader_config.py

    local courses=(course101 course123)
    local admins=(instructor1 instructor2)
    for index in "${!courses[@]}"; do
        local course="${courses[${index}]}"
        local admin="${admins[${index}]}"

        # Get the JupyterHub API token and update the JupyterHub config with it.
        local token=$(get_token "${jupyterhub_root}" "${admin}")
        local config="${jupyterhub_root}/jupyterhub_config.py"
        local new_config=$(sed "s/{{${course}_token}}/${token}/g" "${config}")
        echo "${new_config}" > "${config}"

        # Setup nbgrader configuration for grading account.
        setup_nbgrader "grader-${course}" "${course}_nbgrader_config.py"
        create_course "grader-${course}" "${course}"

        # Enable extensions for grading account.
        enable_create_assignment "grader-${course}"
        enable_formgrader "grader-${course}"
    done

    # Enable extensions for instructors.
    instructors=(instructor1 instructor2)
    for instructor in ${instructors[@]}; do
        enable_assignment_list "${instructor}"
        enable_course_list "${instructor}"
    done

    # Enable extensions for student.
    enable_assignment_list student1
}
