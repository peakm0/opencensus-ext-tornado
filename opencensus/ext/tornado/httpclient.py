import functools

from opencensus.trace.tracer import Tracer
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.span import SpanKind
from opencensus.trace import execution_context

from tornado.httpclient import HTTPRequest, HTTPError


COMPONENT        = COMMON_ATTRIBUTES["COMPONENT"]
HTTP_METHOD      = COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_URL         = COMMON_ATTRIBUTES["HTTP_URL"]
ERROR_MESSAGE    = COMMON_ATTRIBUTES["ERROR_MESSAGE"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]


def _tracer():
    return execution_context.get_opencensus_tracer()


def _normalize_request(args, kwargs):

    req = args[0]
    if not isinstance(req, str):
        # Not a string, no need to force the creation of a HTTPRequest
        return (args, kwargs)

    # keep the original kwargs for calling fetch()
    new_kwargs = {"raise_error": kwargs.pop("raise_error")} if "raise_error" in kwargs else {}

    req = HTTPRequest(req, **kwargs)
    new_args = [req]
    new_args.extend(args[1:])

    # return the normalized args/kwargs
    return (new_args, new_kwargs)


async def fetch_async(func, handler, args, kwargs):

    tracing_enabled = execution_context.get_opencensus_attr("trace_client")
    if not tracing_enabled or \
            len(args) == 0 or hasattr(args[0], "original_request"):
        return await func(*args, **kwargs)

    args, kwargs         = _normalize_request(args, kwargs)
    request              = args[0]
    tracer               = _tracer()
    span_context         = tracer.tracer.span_context
    span_context.span_id = span_context.trace_id # keep current span_context span_id as trace_id to seperate requests as non-hierachical
    span                 = tracer.span(name=request.url)
    span.span_kind       = SpanKind.CLIENT

    for k, v in [
        (COMPONENT  , "HTTP"),
        (HTTP_METHOD, request.method),
        (HTTP_URL   , request.url)
    ]:
        tracer.add_attribute_to_current_span(k, v)

    return await _finish_tracing_callback(func, *args, tracer=tracer, **kwargs)


async def _finish_tracing_callback(func, *args, tracer, **kwargs):

    span = tracer.current_span()
    status_code = None
    try:
        response = await func(*args, **kwargs)
    except Exception as exc:
        error = True
        if isinstance(exc, HTTPError):
            status_code = exc.code
            if status_code < 500:
                error = False
        if error:
            span.add_attribute(ERROR_MESSAGE, repr(exc))
        raise
    status_code = response.code
    if status_code is not None:
        span.add_attribute(HTTP_STATUS_CODE, status_code)
    tracer.end_span()
    return response
