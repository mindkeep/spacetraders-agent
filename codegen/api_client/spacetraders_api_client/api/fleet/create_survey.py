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
        "url": "/my/ships/{ship_symbol}/survey".format(
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
    """Create Survey

     Create surveys on a waypoint that can be extracted such as asteroid fields. A survey focuses on
    specific types of deposits from the extracted location. When ships extract using this survey, they
    are guaranteed to procure a high amount of one of the goods in the survey.

    In order to use a survey, send the entire survey details in the body of the extract request.

    Each survey may have multiple deposits, and if a symbol shows up more than once, that indicates a
    higher chance of extracting that resource.

    Your ship will enter a cooldown after surveying in which it is unable to perform certain actions.
    Surveys will eventually expire after a period of time or will be exhausted after being extracted
    several times based on the survey's size. Multiple ships can use the same survey for extraction.

    A ship must have the `Surveyor` mount installed in order to use this function.

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
    """Create Survey

     Create surveys on a waypoint that can be extracted such as asteroid fields. A survey focuses on
    specific types of deposits from the extracted location. When ships extract using this survey, they
    are guaranteed to procure a high amount of one of the goods in the survey.

    In order to use a survey, send the entire survey details in the body of the extract request.

    Each survey may have multiple deposits, and if a symbol shows up more than once, that indicates a
    higher chance of extracting that resource.

    Your ship will enter a cooldown after surveying in which it is unable to perform certain actions.
    Surveys will eventually expire after a period of time or will be exhausted after being extracted
    several times based on the survey's size. Multiple ships can use the same survey for extraction.

    A ship must have the `Surveyor` mount installed in order to use this function.

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
