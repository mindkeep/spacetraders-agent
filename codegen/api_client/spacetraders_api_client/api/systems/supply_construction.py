from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.supply_construction_body import SupplyConstructionBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    system_symbol: str,
    waypoint_symbol: str,
    *,
    body: SupplyConstructionBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/systems/{system_symbol}/waypoints/{waypoint_symbol}/construction/supply".format(
            system_symbol=quote(str(system_symbol), safe=""),
            waypoint_symbol=quote(str(waypoint_symbol), safe=""),
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
    system_symbol: str,
    waypoint_symbol: str,
    *,
    client: AuthenticatedClient,
    body: SupplyConstructionBody | Unset = UNSET,
) -> Response[Any]:
    """Supply Construction Site

     Supply a construction site with the specified good. Requires a waypoint with a property of
    `isUnderConstruction` to be true.

    The good must be in your ship's cargo. The good will be removed from your ship's cargo and added to
    the construction site's materials.

    Args:
        system_symbol (str):
        waypoint_symbol (str):
        body (SupplyConstructionBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        system_symbol=system_symbol,
        waypoint_symbol=waypoint_symbol,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    system_symbol: str,
    waypoint_symbol: str,
    *,
    client: AuthenticatedClient,
    body: SupplyConstructionBody | Unset = UNSET,
) -> Response[Any]:
    """Supply Construction Site

     Supply a construction site with the specified good. Requires a waypoint with a property of
    `isUnderConstruction` to be true.

    The good must be in your ship's cargo. The good will be removed from your ship's cargo and added to
    the construction site's materials.

    Args:
        system_symbol (str):
        waypoint_symbol (str):
        body (SupplyConstructionBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        system_symbol=system_symbol,
        waypoint_symbol=waypoint_symbol,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
