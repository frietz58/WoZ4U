def is_url(path):
    # determines whether a path is a url or not
    if "http" in path:
        return True
    else:
        return False

def page_load_callback(value):
    # callback for tablet webview page loading, maybe usefull to maintain consistency within gui?
    print("Page load callback: " + str(value))