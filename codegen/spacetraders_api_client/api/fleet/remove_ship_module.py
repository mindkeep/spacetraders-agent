from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.remove_ship_module_body import RemoveShipModuleBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    ship_symbol: str,
    *,
    body: RemoveShipModuleBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/my/ships/{ship_symbol}/modules/remove".format(
            ship_symbol=quote(str(ship_symbol), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    ship_symbol: str,
    *,
    client: AuthenticatedClient | Client,
    body: RemoveShipModuleBody | Unset = UNSET,
) -> Response[Any]:
    """Remove Ship Module

     Remove a module from a ship. The module will be placed in cargo.

    Args:
        ship_symbol (str):
        body (RemoveShipModuleBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        ship_symbol=ship_symbol,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    ship_symbol: str,
    *,
    client: AuthenticatedClient | Client,
    body: RemoveShipModuleBody | Unset = UNSET,
) -> Response[Any]:
    """Remove Ship Module

     Remove a module from a ship. The module will be placed in cargo.

    Args:
        ship_symbol (str):
        body (RemoveShipModuleBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        ship_symbol=ship_symbol,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
