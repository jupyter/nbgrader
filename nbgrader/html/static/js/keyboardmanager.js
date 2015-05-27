function KeyboardManager (obj) {
    this.keycode_to_key = {
        9: 'tab',
        27: 'esc',
        13: 'enter',
        39: 'arrowright',
        37: 'arrowleft'
    };

    this.handlers = new Object();
    this.obj = obj;
}

KeyboardManager.prototype.parseKeybinding = function (keybinding) {
    var parts = keybinding.toLowerCase().split("+");
    var key;
    var shift = false;
    var control = false;
    for (var i = 0; i < parts.length; i++) {
        if (parts[i] === 'ctrl' || parts[i] === 'control') {
            control = true;
        } else if (parts[i] === 'shift') {
            shift = true;
        } else {
            if (key !== undefined) {
                throw new Error("key is already defined");
            }
            key = parts[i];
        }
    }

    return {
        'key': key,
        'shift': shift,
        'control': control
    };
};

KeyboardManager.prototype.constructKeybinding = function (key, control, shift) {
    if (control && shift) {
        return "ctrl+shift+" + key;
    } else if (control) {
        return "ctrl+" + key;
    } else if (shift) {
        return "shift+" + key;
    } else {
        return key;
    }
};

KeyboardManager.prototype.makeSelectorHandler = function (selector) {
    var that = this;
    return function (e) {
        var keycode = that.keycode_to_key[e.which];
        if (keycode) {
            var handler = that.handlers[selector][that.constructKeybinding(keycode, e.ctrlKey, e.shiftKey)];
            if (handler) {
                handler(e);
            }
        }
    };
}

KeyboardManager.prototype.register = function (handler, selector, keybinding) {
    if (this.handlers[selector] === undefined) {
        this.handlers[selector] = new Object();
        $(selector).on('keydown', this.makeSelectorHandler(selector));
    }

    keybinding = this.parseKeybinding(keybinding);
    keybinding = this.constructKeybinding(keybinding.key, keybinding.control, keybinding.shift);
    if (this.obj) {
        this.handlers[selector][keybinding] = handler.bind(this.obj);
    } else {
        this.handlers[selector][keybinding] = handler;
    }
};
