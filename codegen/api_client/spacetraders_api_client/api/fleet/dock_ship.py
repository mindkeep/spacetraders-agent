from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import Response


def _get_kwargs(
    ship_symbol: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/my/ships/{ship_symbol}/dock".format(
            ship_symbol=quote(str(ship_symbol), safe=""),
        ),
    }

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
) -> Response[Any]:
    """Dock Ship

     Attempt to dock your ship at its current location. Docking will only succeed if your ship is capable
    of docking at the time of the request.

    Docked ships can access elements in their current location, such as the market or a shipyard, but
    cannot do actions that require the ship to be above surface such as navigating or extracting.

    The endpoint is idempotent - successive calls will succeed even if the ship is already docked.

    Args:
        ship_symbol (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        ship_symbol=ship_symbol,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    ship_symbol: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any]:
    """Dock Ship

     Attempt to dock your ship at its current location. Docking will only succeed if your ship is capable
    of docking at the time of the request.

    Docked ships can access elements in their current location, such as the market or a shipyard, but
    cannot do actions that require the ship to be above surface such as navigating or extracting.

    The endpoint is idempotent - successive calls will succeed even if the ship is already docked.

    Args:
        ship_symbol (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        ship_symbol=ship_symbol,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
