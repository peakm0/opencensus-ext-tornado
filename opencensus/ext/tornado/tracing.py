import functools
import wrapt
import sys
from inspect import iscoroutine

from opencensus.trace.tracer import Tracer
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.span import SpanKind
from opencensus.trace import execution_context


async def maybe_future(fn, *args, **kwargs):
    result = fn(*args, **kwargs)
    return await result if iscoroutine(result) else result


COMPONENT        = COMMON_ATTRIBUTES["COMPONENT"]
HTTP_HOST        = COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD      = COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_URL         = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_PATH        = COMMON_ATTRIBUTES["HTTP_PATH"]
ERROR_MESSAGE    = COMMON_ATTRIBUTES["ERROR_MESSAGE"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]


class TornadoTracing(object):

    def __init__(self, tracer=None, sampler=None):
        _tracer_obj = tracer or Tracer(sampler=(sampler or AlwaysOnSampler()))
        execution_context.set_opencensus_tracer(_tracer_obj)

    @property
    def _tracer(self):
        return execution_context.get_opencensus_tracer()

    async def trace(self, *attributes):

        @wrapt.decorator
        async def wrapper(wrapped, instance, args, kwargs):
            trace_all = execution_context.get_opencensus_attr("trace_all")
            if trace_all:
                return maybe_future(wrapped, *args, **kwargs)
            handler = instance
            try:
                self._start_tracing(handler, list(attributes))
                # Run the actual function.
                result = maybe_future(wrapped, *args, **kwargs)
                self._finish_tracing(handler)
            except Exception as exc:
                self._finish_tracing(handler, error=exc)
                raise
            return result
        return wrapper

    def _start_tracing(self, handler, attributes):

        headers = handler.request.headers
        request = handler.request

        # keep current span_context as trace_id to seperate requests as non-hierachical
        span_context = self._tracer.tracer.span_context
        span_context.span_id = span_context.trace_id

        # start span
        span = self._tracer.span(name=request.path)
        span.span_kind = SpanKind.SERVER

        # log any traced attributes
        for k, v in [
            (COMPONENT  , "HTTP"),
            (HTTP_HOST  , request.host),
            (HTTP_METHOD, request.method),
            (HTTP_URL   , request.uri),
            (HTTP_PATH  , request.path)
        ]:
            self._tracer.add_attribute_to_current_span(k, v)

        for attr in attributes:
            if hasattr(request, attr):
                payload = str(getattr(request, attr))
                if payload:
                    self._tracer.add_attribute_to_current_span(attr, payload)

    def _finish_tracing(self, handler, error=None):

        attr_tuple = (ERROR_MESSAGE, repr(error)) if error is not None else \
            (HTTP_STATUS_CODE, handler.get_status())
        self._tracer.add_attribute_to_current_span(*attr_tuple)
        self._tracer.end_span()
