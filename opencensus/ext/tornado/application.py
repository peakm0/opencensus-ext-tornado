import importlib

from opencensus.trace import execution_context

from . import httpclient
from .tracing import TornadoTracing


DEFAULT_TRACE_ALL = True
DEFAULT_TRACE_CLIENT = True


def _get_callable_from_name(full_name):
    mod_name, func_name = full_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, func_name, None)


def tracer_config(__init__, app, args, kwargs):
    """
    Wraps the Tornado web application initialization so that the
    TornadoTracing instance is created around an OpenCensus-compatible tracer.
    """
    __init__(*args, **kwargs)

    tracing           = app.settings.get("opencensus_tracing")
    tracer_callable   = app.settings.get("opencensus_tracer_callable")
    tracer_parameters = app.settings.get("opencensus_tracer_parameters") or {}
    trace_all         = app.settings.get("opencensus_trace_all", DEFAULT_TRACE_ALL)
    trace_client      = app.settings.get("opencensus_trace_client", DEFAULT_TRACE_CLIENT)
    blacklist_paths   = app.settings.get("opencensus_blacklist_paths") or []

    if tracer_callable is not None:
        if not callable(tracer_callable):
            tracer_callable = _get_callable_from_name(tracer_callable)

        tracer = tracer_callable(**tracer_parameters)
        tracing = TornadoTracing(tracer)

    if tracing is None:
        tracing = TornadoTracing()  # fallback to the global tracer

    app.settings["opencensus_tracing"] = tracing

    # set variables in execution context
    execution_context.set_opencensus_attr("tracing", tracing)
    execution_context.set_opencensus_attr("trace_client", trace_client)
    execution_context.set_opencensus_attr("trace_all", trace_all)
    execution_context.set_opencensus_attr("blacklist_paths", blacklist_paths)
