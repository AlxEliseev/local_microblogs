from typing import Callable, Any
import logging
from functools import wraps

router_logger = logging.getLogger("router_logger")
crud_logger = logging.getLogger("crud_logger")


def router_logging(http_method: str, route_path: str) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        async def inner(*args, **kwargs):  # noqa: WPS430
            clean_kwargs = {
                kw_name: kw_value
                for kw_name, kw_value in kwargs.items()
                if isinstance(
                    kw_value, (str, int, float, bool, dict, list, None.__class__)
                )
            }
            log = {
                "route": route_path,
                "http_method": http_method,
                "kwargs": clean_kwargs,
            }
            router_logger.info(f"ROUTE STARTS: {log}")
            try:
                func_result = await func(*args, **kwargs)
            except Exception as exc:
                router_logger.error(
                    f"ROUTE ERROR in {route_path} | Error: {str(exc)}", exc_info=True
                )
                raise exc
            return func_result

        return inner

    return wrapper


def crud_logging(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs) -> Any:
        class_name = args[0].__class__.__name__
        method_name = f"{class_name}.{func.__name__}"
        crud_logger.debug(f"CRUD METHOD '{method_name}' " f"WITH ARGS {kwargs} RUNS")
        rv = await func(*args, **kwargs)
        crud_logger.debug(f"CRUD METHOD '{method_name}' " f"RETURNS {rv}")
        return rv

    return wrapper
