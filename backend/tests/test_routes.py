import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/tweets", "/api/users/me",
                                   "/api/users/<id>"])
async def test_route_status(app_client, route):
    rv = await app_client.get(route)
    assert rv.status_code == 200