var keycode_to_key = {
    9: 'TAB',
    27: 'ESCAPE',
    13: 'ENTER',
    39: 'RIGHT_ARROW',
    37: 'LEFT_ARROW'
};

var handlers = new Object();
var register_handler = function(selector, key, handler) {
    if (handlers[selector] === undefined) {
        handlers[selector] = new Object();
        $(selector).on('keydown', function(e) {
            var key = keycode_to_key[e.keyCode || e.which];
            var handler = handlers[selector][key];
            if (handler) {
                handler(e);
            }
        });
    }

    handlers[selector][key] = handler;
};
