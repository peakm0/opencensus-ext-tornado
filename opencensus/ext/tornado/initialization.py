import tornado
from wrapt import wrap_function_wrapper as wrap_function, ObjectProxy

from . import application, handlers, httpclient

def init_tracing():
    _patch_tornado()
    _patch_tornado_client()

def init_client_tracing(tracer=None):
    _patch_tornado_client()

def _patch_tornado():
    # patch only once
    if getattr(tornado, "__opentracing_patch", False) is True:
        return

    setattr(tornado, "__opentracing_patch", True)

    wrap_function("tornado.web", "Application.__init__",
                  application.tracer_config)

    wrap_function("tornado.web", "RequestHandler._execute",
                  handlers.execute)
    wrap_function("tornado.web", "RequestHandler.on_finish",
                  handlers.on_finish)
    wrap_function("tornado.web", "RequestHandler.log_exception",
                  handlers.log_exception)


def _patch_tornado_client():
    if getattr(tornado, "__opentracing_client_patch", False) is True:
        return

    setattr(tornado, "__opentracing_client_patch", True)

    wrap_function("tornado.httpclient", "AsyncHTTPClient.fetch",
                  httpclient.fetch_async)


def _unpatch(obj, attr):
    f = getattr(obj, attr, None)
    if f and isinstance(f, ObjectProxy) and hasattr(f, "__wrapped__"):
        setattr(obj, attr, f.__wrapped__)


def _unpatch_tornado():
    if getattr(tornado, "__opentracing_patch", False) is False:
        return

    setattr(tornado, "__opentracing_patch", False)

    _unpatch(tornado.web.Application, "__init__")

    _unpatch(tornado.web.RequestHandler, "_execute")
    _unpatch(tornado.web.RequestHandler, "on_finish")
    _unpatch(tornado.web.RequestHandler, "log_exception")


def _unpatch_tornado_client():
    if getattr(tornado, "__opentracing_client_patch", False) is False:
        return

    setattr(tornado, "__opentracing_client_patch", False)

    _unpatch(tornado.httpclient.AsyncHTTPClient, "fetch")
