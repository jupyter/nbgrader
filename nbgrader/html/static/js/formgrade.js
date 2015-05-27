function FormGrader (base_url, submission_id) {

    this.base_url = base_url;
    this.submission_id = submission_id;

    this.current_index;
    this.last_selected;

    this.grades;
    this.comments;
}

FormGrader.prototype.init = function () {
    this.grades = loadGrades(this.submission_id);
    this.comments = loadComments(this.submission_id);

    this.configureTooltips();
    this.configureTabbing();
    this.configureNavigation();
    this.configureScrolling();
}

FormGrader.prototype.navigateTo = function (location) {
    return this.base_url + '/submissions/' + this.submission_id + '/' + location + '?index=' + this.current_index;
};

FormGrader.prototype.nextAssignment = function () {
    window.location = this.navigateTo('next');
};

FormGrader.prototype.nextIncorrectAssignment = function () {
    window.location = this.navigateTo('next_incorrect');
};

FormGrader.prototype.prevAssignment = function () {
    window.location = this.navigateTo('prev');
};

FormGrader.prototype.prevIncorrectAssignment = function () {
    window.location = this.navigateTo('prev_incorrect');
};

FormGrader.prototype.save = function (callback) {
    var elem = document.activeElement;
    if (elem.tagName === "INPUT" || elem.tagName === "TEXTAREA") {
        $(document).on("finished_saving", callback);
        $(elem).blur();
        $(elem).trigger("change");
    } else {
        callback();
    }
};

FormGrader.prototype.getScrollPosition = function () {
    var target = this.last_selected.parents(".nbgrader_cell");
    if (target.length == 0) {
        return $("body").offset().top;
    } else {
        return target.offset().top - $(window).height() * 0.33 + 60;
    }
};

FormGrader.prototype.getIndex = function (elem) {
    if (elem !== undefined) {
        var elems = $(".tabbable");
        return elems.index(elem);
    } else {
        return parseInt(getParameterByName(index)) || 0;
    }
};

FormGrader.prototype.selectNext = function (target, shift) {
    var index, elems;
    elems = $(".tabbable");
    if (shift) {
        index = this.getIndex(target) - 1;
    } else {
        index = this.getIndex(target) + 1;
    }
    if (index === elems.length) {
        index = 0;
    } else if (index === -1) {
        index = elems.length - 1;
    }
    $(elems[index]).select();
    $(elems[index]).focus();
};

FormGrader.prototype.configureTooltips = function () {
    $("li.previous a").tooltip({container: 'body'});
    $("li.next a").tooltip({container: 'body'});
    $("li.live-notebook a").tooltip({container: 'body'});
};

FormGrader.prototype.configureTabbing = function () {
    var that = this;

    // disable link selection on tabs
    $('a:not(.tabbable)').attr('tabindex', '-1');

    register_handler(".tabbable", "TAB", function (e) {
        e.preventDefault();
        e.stopPropagation();
        that.selectNext(e.currentTarget, e.shiftKey);
    });

    register_handler("body", "TAB", function (e) {
        e.preventDefault();
        that.selectNext(that.last_selected, e.shiftKey);
    });

    register_handler(".tabbable", "ESCAPE", function (e) {
        $(e.currentTarget).blur();
    });

    register_handler("body", "ENTER", function (e) {
        if (that.last_selected[0] !== document.activeElement) {
            e.preventDefault();
            e.stopPropagation();

            $("body, html").scrollTop(that.getScrollPosition());
            that.last_selected.select();
            that.last_selected.focus();
        }
    });
};

FormGrader.prototype.setIndexFromUrl = function () {
    var name = "index";

    // http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    var index = results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));

    this.setCurrentIndex(parseInt(index) || 0);
    this.last_selected = $($(".tabbable")[this.current_index]);
};

FormGrader.prototype.setCurrentIndex = function (index) {
    // if an index is not provided, then we compute it based
    // on whatver the most recently selected element was
    if (index === undefined) {
        var target = this.last_selected.parents(".nbgrader_cell").find(".score");
        if (target.length == 0) {
            this.current_index = this.getIndex(this.last_selected);
        } else {
            this.current_index = this.getIndex(target);
        }

    // otherwise we do some value checking and just set the
    // value directly
    } else {
        if (index < 0) {
            this.current_index = 0;
        } else if (index > $(".tabbable").length) {
            this.current_index = $(".tabbable").length;
        } else {
            this.current_index = index;
        }
    }
};

FormGrader.prototype.configureScrolling = function () {
    var that = this;

    $(".tabbable").focus(function (event) {
        that.last_selected = $(event.currentTarget);
        that.setCurrentIndex();
        history.replaceState(history.state, "", that.navigateTo(""));
        $("body, html").stop().animate({
            scrollTop: that.getScrollPosition()
        }, 500);
    });

    this.setIndexFromUrl();

    MathJax.loaded = false;
    MathJax.Hub.Startup.signal.Interest(function (message) {
        if (message === "End") {
            that.last_selected.select();
            that.last_selected.focus();
            MathJax.loaded = true;
        }
    });
};

FormGrader.prototype.configureNavigation = function () {
    var that = this;

    register_handler("body", "RIGHT_ARROW", function (e) {
        if (e.shiftKey && e.ctrlKey) {
            that.save(function () {
                that.nextIncorrectAssignment();
            });
        } else if (e.shiftKey) {
            that.save(function () {
                that.nextAssignment();
            });
        }
    });

    register_handler("body", "LEFT_ARROW", function (e) {
        if (e.shiftKey && e.ctrlKey) {
            that.save(function () {
                that.prevIncorrectAssignment();
            });
        } else if (e.shiftKey) {
            that.save(function () {
                that.prevAssignment();
            });
        }
    });
};

var formgrader = new FormGrader(base_url, submission_id);
$(window).load(function () {
    formgrader.init()
});
