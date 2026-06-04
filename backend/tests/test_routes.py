import pytest
import json


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/tweets", "/api/users/me",
                                   "/api/users/2"])
async def test_route_status(app_client, seed_data, route):
    """Все GET роуты должны вернуть 200"""
    rv = await app_client.get(route, headers={"api-key": "1"})
    assert rv.status_code == 200

@pytest.mark.asyncio
async def test_post_follow(app_client, seed_data):
    """POST запрос должен заффоловить другого пользователя"""
    rv = await app_client.post("/api/users/2/follow", headers={"api-key": "1"})
    assert json.loads(rv.content) == {"result": True}
    assert rv.status_code == 200

@pytest.mark.asyncio
async def test_post_follow_double_follow_exception(app_client, seed_data):
    """Повторный фоллов должен выбросить исключение"""
    rv = await app_client.post("/api/users/1/follow", headers={"api-key": "2"})
    assert json.loads(rv.content) == {"result": False, "message": "Already following this user"}
    assert rv.status_code == 409

@pytest.mark.asyncio
async def test_delete_follow(app_client, seed_data):
    """Unfollow пользователя должен вернуть 200"""
    rv = await app_client.delete("/api/users/1/follow", headers={"api-key": "2"})
    assert json.loads(rv.content) == {"result": True}
    assert rv.status_code == 200

@pytest.mark.asyncio
async def test_delete_follow_no_follow_exception(app_client, seed_data):
    """Если пытаемся unfollow того, кого не фолловим, должно вернуться 404"""
    rv = await app_client.delete("/api/users/2/follow", headers={"api-key": "1"})
    assert json.loads(rv.content) == {"result": False, "message": "No such follow in database"}
    assert rv.status_code == 404

@pytest.mark.asyncio
async def test_get_me(app_client, seed_data):
    """Должен вывести информацию о текущем пользователе"""
    rv = await app_client.get("/api/users/me", headers={"api-key": "2"})
    assert rv.status_code == 200
    assert json.loads(rv.content) == {"result": True,
                                      "user":{
                                          "id": 2,
                                          "name": "user2",
                                          "followers": [],
                                          "following": [
                                              {
                                                  "id": 1,
                                                  "name": "user1"
                                              }
                                          ]
                                      }
                                      }

@pytest.mark.asyncio
async def test_get_user(app_client, seed_data):
    """Должен вывести информацию о пользователе по id"""
    rv = await app_client.get("/api/users/1", headers={"api-key": "2"})
    assert rv.status_code == 200
    assert json.loads(rv.content) == {"result": True,
                                      "user":{
                                          "id": 1,
                                          "name": "user1",
                                          "followers": [
                                              {
                                                  "id": 2,
                                                  "name": "user2"
                                              }
                                          ],
                                          "following": []
                                      }
                                      }