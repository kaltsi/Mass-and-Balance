/* Dark mode toggle, shared by the landing page and the sheets.

   The choice is stored under one key, so every sheet and the landing page use
   the same theme. Without a stored choice the system preference decides.
*/

var g_theme_key = "kaltsi.mb.theme";

/* The entry says what selecting it does, in the sheet language. */
function theme_labels() {
    return (document.documentElement.getAttribute("data-theme") == "dark")
        ? ["Light mode", "Vaalea tila"]
        : ["Dark mode", "Tumma tila"];
}

function saved_theme() {
    if (typeof(Storage) !== "undefined") {
        var t = localStorage.getItem(g_theme_key);
        if (t == "light" || t == "dark") {
            return t;
        }
    }

    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
    }
    return "light";
}

function paint_theme(theme) {
    document.documentElement.setAttribute("data-theme", theme);

    var button = document.getElementById("theme_toggle");
    if (button !== null) {
        button.title = (theme == "dark") ? "Switch to light mode" : "Switch to dark mode";
    }

    /* In the sheet the theme is an entry in the Settings dropdown. */
    var option = document.getElementById("select_settings_theme");
    if (option !== null) {
        var lang = (typeof(g_defs) != "undefined") ? g_defs.s.lang : 0;
        option.textContent = theme_labels()[lang];
    }
}

function toggle_theme() {
    var theme = (document.documentElement.getAttribute("data-theme") == "dark") ? "light" : "dark";

    if (typeof(Storage) !== "undefined") {
        localStorage.setItem(g_theme_key, theme);
    }

    paint_theme(theme);
}

function setup_theme() {
    paint_theme(saved_theme());
}
