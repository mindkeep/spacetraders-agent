from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.install_mount_install_mount_request import InstallMountInstallMountRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    ship_symbol: str,
    *,
    body: InstallMountInstallMountRequest | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/my/ships/{ship_symbol}/mounts/install".format(
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
    body: InstallMountInstallMountRequest | Unset = UNSET,
) -> Response[Any]:
    """Install Mount

     Install a mount on a ship.

    In order to install a mount, the ship must be docked and located in a waypoint that has a `Shipyard`
    trait. The ship also must have the mount to install in its cargo hold.

    An installation fee will be deduced by the Shipyard for installing the mount on the ship.

    Args:
        ship_symbol (str):
        body (InstallMountInstallMountRequest | Unset):

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
    body: InstallMountInstallMountRequest | Unset = UNSET,
) -> Response[Any]:
    """Install Mount

     Install a mount on a ship.

    In order to install a mount, the ship must be docked and located in a waypoint that has a `Shipyard`
    trait. The ship also must have the mount to install in its cargo hold.

    An installation fee will be deduced by the Shipyard for installing the mount on the ship.

    Args:
        ship_symbol (str):
        body (InstallMountInstallMountRequest | Unset):

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
