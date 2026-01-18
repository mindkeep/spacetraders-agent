from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.deliver_contract_body import DeliverContractBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    contract_id: str,
    *,
    body: DeliverContractBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/my/contracts/{contract_id}/deliver".format(
            contract_id=quote(str(contract_id), safe=""),
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
    contract_id: str,
    *,
    client: AuthenticatedClient,
    body: DeliverContractBody | Unset = UNSET,
) -> Response[Any]:
    """Deliver Cargo to Contract

     Deliver cargo to a contract.

    In order to use this API, a ship must be at the delivery location (denoted in the delivery terms as
    `destinationSymbol` of a contract) and must have a number of units of a good required by this
    contract in its cargo.

    Cargo that was delivered will be removed from the ship's cargo.

    Args:
        contract_id (str):
        body (DeliverContractBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        contract_id=contract_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    contract_id: str,
    *,
    client: AuthenticatedClient,
    body: DeliverContractBody | Unset = UNSET,
) -> Response[Any]:
    """Deliver Cargo to Contract

     Deliver cargo to a contract.

    In order to use this API, a ship must be at the delivery location (denoted in the delivery terms as
    `destinationSymbol` of a contract) and must have a number of units of a good required by this
    contract in its cargo.

    Cargo that was delivered will be removed from the ship's cargo.

    Args:
        contract_id (str):
        body (DeliverContractBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        contract_id=contract_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
