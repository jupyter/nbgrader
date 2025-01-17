c = get_config()

c.ServerApp.tornado_settings = {}
c.ServerApp.tornado_settings["headers"] = {
    "Content-Security-Policy": "frame-ancestors 'self'"
}