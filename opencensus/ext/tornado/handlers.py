from tornado.web import HTTPError
from opencensus.trace import execution_context
from opencensus.trace.utils import disable_tracing_url

async def execute(func, handler, args, kwargs):

    attrs           = execution_context.get_opencensus_attrs()
    tracing         = attrs.get("tracing")
    trace_all       = attrs.get("trace_all")
    blacklist_paths = attrs.get("blacklist_paths")

    if trace_all and "/" in handler.request.uri and not disable_tracing_url(handler.request.uri, blacklist_paths):
        attrs = handler.settings.get('opencensus_traced_attributes', [])
        tracing._start_tracing(handler, attrs)

    return await func(*args, **kwargs)


def on_finish(func, handler, args, kwargs):

    attrs           = execution_context.get_opencensus_attrs()
    tracing         = attrs.get("tracing")
    trace_all       = attrs.get("trace_all")
    blacklist_paths = attrs.get("blacklist_paths")

    if trace_all and "/" in handler.request.uri and not disable_tracing_url(handler.request.uri, blacklist_paths):
        tracing._finish_tracing(handler)

    return func(*args, **kwargs)


def log_exception(func, handler, args, kwargs):
    """
    Wrap the handler ``log_exception`` method to finish the Span for the
    given request, if available. This method is called when an Exception
    is not handled in the user code.
    """
    # safe-guard: expected arguments -> log_exception(self, typ, value, tb)
    value = args[1] if len(args) == 3 else None
    if value is None:
        return func(*args, **kwargs)

    tracing = execution_context.get_opencensus_attr('tracing')
    if not isinstance(value, HTTPError) or 500 <= value.status_code <= 599:
        tracing._finish_tracing(handler, error=value)

    return func(*args, **kwargs)
