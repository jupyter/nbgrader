/*
 * Module of data to send to Jupyterlab's nbgrader extension to perform actions.
 */

var jlab_go_to_path = function(directory_path){
    return JSON.stringify({
               "command": "filebrowser:go-to-path",
               "arguments": {"path": directory_path}
           });
}