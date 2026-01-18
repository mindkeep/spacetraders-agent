from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.refuel_ship_body import RefuelShipBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    ship_symbol: str,
    *,
    body: RefuelShipBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/my/ships/{ship_symbol}/refuel".format(
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
    client: AuthenticatedClient,
    body: RefuelShipBody | Unset = UNSET,
) -> Response[Any]:
    """Refuel Ship

     Refuel your ship by buying fuel from the local market.

    Requires the ship to be docked in a waypoint that has the `Marketplace` trait, and the market must
    be selling fuel in order to refuel.

    Each fuel bought from the market replenishes 100 units in your ship's fuel.

    Ships will always be refuel to their frame's maximum fuel capacity when using this action.

    Args:
        ship_symbol (str):
        body (RefuelShipBody | Unset):

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
    client: AuthenticatedClient,
    body: RefuelShipBody | Unset = UNSET,
) -> Response[Any]:
    """Refuel Ship

     Refuel your ship by buying fuel from the local market.

    Requires the ship to be docked in a waypoint that has the `Marketplace` trait, and the market must
    be selling fuel in order to refuel.

    Each fuel bought from the market replenishes 100 units in your ship's fuel.

    Ships will always be refuel to their frame's maximum fuel capacity when using this action.

    Args:
        ship_symbol (str):
        body (RefuelShipBody | Unset):

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
