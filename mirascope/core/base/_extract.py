"""The `extract_factory` method for generating provider specific create decorators."""

import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar, overload

from pydantic import BaseModel, ValidationError

from ._create import create_factory
from ._utils import (
    BaseType,
    GetJsonOutput,
    SetupCall,
    extract_tool_return,
    setup_extract_tool,
)
from ._utils._protocols import fn_is_async, fn_is_sync
from .call_params import BaseCallParams
from .call_response import BaseCallResponse
from .dynamic_config import BaseDynamicConfig
from .tool import BaseTool

_BaseCallResponseT = TypeVar("_BaseCallResponseT", bound=BaseCallResponse)
_BaseClientT = TypeVar("_BaseClientT", bound=object)
_BaseDynamicConfigT = TypeVar("_BaseDynamicConfigT", bound=BaseDynamicConfig)
_ParsedOutputT = TypeVar("_ParsedOutputT")
_BaseCallParamsT = TypeVar("_BaseCallParamsT", bound=BaseCallParams)
_ResponseT = TypeVar("_ResponseT")
_ResponseChunkT = TypeVar("_ResponseChunkT")
_BaseToolT = TypeVar("_BaseToolT", bound=BaseTool)
_ResponseModelT = TypeVar("_ResponseModelT", bound=BaseModel | BaseType)
_P = ParamSpec("_P")
_BaseMessageT = TypeVar("_BaseMessageT", bound=dict)


def extract_factory(  # noqa: ANN202
    *,
    TCallResponse: type[_BaseCallResponseT],
    TToolType: type[BaseTool],
    setup_call: SetupCall[
        _BaseClientT,
        _BaseDynamicConfigT,
        _BaseCallParamsT,
        _ResponseT,
        _ResponseChunkT,
        _BaseToolT,
    ],
    get_json_output: GetJsonOutput[_BaseCallResponseT],
):
    """Returns the wrapped function with the provider specific interfaces."""
    create_decorator = create_factory(
        TCallResponse=TCallResponse, setup_call=setup_call
    )

    @overload
    def decorator(
        fn: Callable[_P, _BaseDynamicConfigT],
        model: str,
        response_model: type[_ResponseModelT],
        output_parser: Callable[[_ResponseModelT], _ParsedOutputT] | None,
        json_mode: bool,
        client: _BaseClientT | None,
        call_params: _BaseCallParamsT,
    ) -> Callable[_P, _ResponseModelT | _ParsedOutputT]: ...

    @overload
    def decorator(
        fn: Callable[_P, Awaitable[_BaseDynamicConfigT]],
        model: str,
        response_model: type[_ResponseModelT],
        output_parser: Callable[[_ResponseModelT], _ParsedOutputT] | None,
        json_mode: bool,
        client: _BaseClientT | None,
        call_params: _BaseCallParamsT,
    ) -> Callable[_P, Awaitable[_ResponseModelT | _ParsedOutputT]]: ...

    def decorator(
        fn: Callable[_P, _BaseDynamicConfigT]
        | Callable[_P, Awaitable[_BaseDynamicConfigT]],
        model: str,
        response_model: type[_ResponseModelT],
        output_parser: Callable[[_ResponseModelT], _ParsedOutputT] | None,
        json_mode: bool,
        client: _BaseClientT | None,
        call_params: _BaseCallParamsT,
    ) -> Callable[
        _P,
        _ResponseModelT | _ParsedOutputT | Awaitable[_ResponseModelT | _ParsedOutputT],
    ]:
        tool = setup_extract_tool(response_model, TToolType)
        create_decorator_kwargs = {
            "model": model,
            "tools": [tool],
            "output_parser": None,
            "json_mode": json_mode,
            "client": client,
            "call_params": call_params,
        }

        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def inner_async(
                *args: _P.args, **kwargs: _P.kwargs
            ) -> _ResponseModelT:
                assert fn_is_async(fn)
                call_response = await create_decorator(
                    fn=fn, **create_decorator_kwargs
                )(*args, **kwargs)
                json_output = get_json_output(call_response, json_mode)
                try:
                    output = extract_tool_return(response_model, json_output, False)
                except ValidationError as e:
                    e._response = call_response  # type: ignore
                    raise e
                if isinstance(output, BaseModel):
                    output._response = call_response  # type: ignore
                return output if not output_parser else output_parser(output)

            return inner_async
        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _ResponseModelT:
                if fn_is_sync(fn):
                    call_response = create_decorator(fn=fn, **create_decorator_kwargs)(
                        *args, **kwargs
                    )
                    json_output = get_json_output(call_response, json_mode)
                    try:
                        output = extract_tool_return(response_model, json_output, False)
                    except ValidationError as e:
                        e._response = call_response  # type: ignore
                        raise e
                    if isinstance(output, BaseModel):
                        output._response = call_response  # type: ignore
                    return output if not output_parser else output_parser(output)  # type: ignore
                else:  # pragma: no cover
                    raise AssertionError("Function must be async")

            return inner

    return decorator
