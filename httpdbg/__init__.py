__version__ = "2.1.4"

__all__ = ["export_html", "httprecord", "HTTPRecords"]


# lazy loading to avoid circular import issue
def __getattr__(name):
    if name == "export_html":
        from httpdbg.export import export_html

        return export_html
    if name == "httprecord":
        from httpdbg.hooks.all import httprecord

        return httprecord
    if name == "HTTPRecords":
        from httpdbg.records import HTTPRecords

        return HTTPRecords
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
