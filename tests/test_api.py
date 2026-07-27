import pytest
import mongomock
from unittest.mock import patch

# Mock MongoDB before importing app modules
with patch("db.MongoClient", mongomock.MongoClient):
    from app import create_app

@pytest.fixture
def client():
    mongo_client = mongomock.MongoClient()
    with patch("db.get_db", return_value=mongo_client["test_journal_db"]):
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"

def test_global_error_handlers(client):
    # Test 404 Not Found JSON response
    res_404 = client.get("/api/non_existent_route")
    assert res_404.status_code == 404
    assert res_404.get_json()["success"] is False
    assert "not found" in res_404.get_json()["error"].lower()

    # Test 405 Method Not Allowed JSON response
    res_405 = client.post("/api/health")
    assert res_405.status_code == 405
    assert res_405.get_json()["success"] is False
    assert "method not allowed" in res_405.get_json()["error"].lower()

def test_full_journal_workflow_and_edge_cases(client):
    # 1. Signup user
    signup_res = client.post("/api/auth/signup", json={
        "username": "Journal_User",
        "email": "user@example.com",
        "password": "securepassword123"
    })
    assert signup_res.status_code == 201
    signup_json = signup_res.get_json()
    assert signup_json["success"] is True
    token = signup_json["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Duplicate signup check with different casing (tests case-insensitivity fix)
    dup_res = client.post("/api/auth/signup", json={
        "username": "JOURNAL_USER",
        "email": "USER@EXAMPLE.COM",
        "password": "securepassword123"
    })
    assert dup_res.status_code == 400
    assert dup_res.get_json()["success"] is False

    # 3. Login with mixed-case username
    login_res = client.post("/api/auth/login", json={
        "username": "journal_user",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    login_json = login_res.get_json()
    assert login_json["success"] is True
    assert "token" in login_json

    # 4. Get Current User Profile
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    me_json = me_res.get_json()
    assert me_json["data"]["username"] == "Journal_User"

    # 5. Create Private Journal Entry
    priv_res = client.post("/api/journals", json={
        "title": "Secret Thoughts",
        "content": "This is a private journal entry.",
        "tags": ["personal", "secret", ""],
        "is_public": False
    }, headers=auth_headers)
    assert priv_res.status_code == 201
    priv_json = priv_res.get_json()
    priv_post = priv_json["data"]
    assert priv_post["is_public"] is False
    priv_id = priv_post["id"]

    # 6. Create Public Journal Entry
    pub_res = client.post("/api/journals", json={
        "title": "Hello World Journal",
        "content": "Sharing my thoughts with everyone!",
        "tags": ["community", "ideas"],
        "is_public": True
    }, headers=auth_headers)
    assert pub_res.status_code == 201
    pub_json = pub_res.get_json()
    pub_post = pub_json["data"]
    assert pub_post["is_public"] is True
    pub_id = pub_post["id"]

    # 7. Check Public Feed - Should contain public post, NOT private post
    feed_res = client.get("/api/journals/feed")
    assert feed_res.status_code == 200
    feed_posts = feed_res.get_json()["data"]
    assert len(feed_posts) == 1
    assert feed_posts[0]["id"] == pub_id

    # 8. Check User's My Journals
    my_res = client.get("/api/journals/my", headers=auth_headers)
    assert my_res.status_code == 200
    assert len(my_res.get_json()["data"]) == 2

    # 9. Test empty title update validation error
    invalid_update = client.put(f"/api/journals/{pub_id}", json={
        "title": "   "
    }, headers=auth_headers)
    assert invalid_update.status_code == 400
    assert "title cannot be empty" in invalid_update.get_json()["error"].lower()

    # 10. Toggle Privacy: Change Private -> Public
    toggle_pub_res = client.patch(f"/api/journals/{priv_id}/privacy", json={
        "is_public": True
    }, headers=auth_headers)
    assert toggle_pub_res.status_code == 200
    assert toggle_pub_res.get_json()["data"]["is_public"] is True

    # 11. Delete Journal Entry
    del_res = client.delete(f"/api/journals/{pub_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # 12. Verify post is deleted
    my_res_after_del = client.get("/api/journals/my", headers=auth_headers)
    assert len(my_res_after_del.get_json()["data"]) == 1

def test_journal_reactions_workflow(client):
    # 1. Signup Author User
    signup1 = client.post("/api/auth/signup", json={
        "username": "AuthorUser",
        "email": "author@example.com",
        "password": "password123"
    })
    token1 = signup1.get_json()["token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 2. Signup Reactor User
    signup2 = client.post("/api/auth/signup", json={
        "username": "ReactorUser",
        "email": "reactor@example.com",
        "password": "password123"
    })
    token2 = signup2.get_json()["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 3. Author creates a public journal post
    post_res = client.post("/api/journals", json={
        "title": "Reactable Journal",
        "content": "Feel free to react to this post!",
        "is_public": True
    }, headers=headers1)
    post_id = post_res.get_json()["data"]["id"]
    initial_post = post_res.get_json()["data"]
    assert initial_post["total_reactions"] == 0
    assert initial_post["reaction_counts"] == {}

    # 4. ReactorUser reacts with "like"
    react_like = client.post(f"/api/journals/{post_id}/react", json={
        "type": "like"
    }, headers=headers2)
    assert react_like.status_code == 200
    like_data = react_like.get_json()["data"]
    assert like_data["action"] == "added"
    assert like_data["user_reaction"] == "like"
    assert like_data["reaction_counts"] == {"like": 1}
    assert like_data["total_reactions"] == 1

    # 5. ReactorUser changes reaction from "like" to "fire"
    react_fire = client.post(f"/api/journals/{post_id}/react", json={
        "type": "fire"
    }, headers=headers2)
    assert react_fire.status_code == 200
    fire_data = react_fire.get_json()["data"]
    assert fire_data["action"] == "updated"
    assert fire_data["user_reaction"] == "fire"
    assert fire_data["reaction_counts"] == {"fire": 1}
    assert fire_data["total_reactions"] == 1

    # 6. AuthorUser also reacts with "fire"
    author_fire = client.post(f"/api/journals/{post_id}/react", json={
        "type": "fire"
    }, headers=headers1)
    assert author_fire.status_code == 200
    assert author_fire.get_json()["data"]["reaction_counts"] == {"fire": 2}
    assert author_fire.get_json()["data"]["total_reactions"] == 2

    # 7. Check public feed for ReactorUser - should show total_reactions=2 and user_reaction="fire"
    feed_res = client.get("/api/journals/feed", headers=headers2)
    feed_post = feed_res.get_json()["data"][0]
    assert feed_post["total_reactions"] == 2
    assert feed_post["reaction_counts"] == {"fire": 2}
    assert feed_post["user_reaction"] == "fire"

    # 8. Get reaction details breakdown
    detail_reactions = client.get(f"/api/journals/{post_id}/reactions")
    assert detail_reactions.status_code == 200
    r_detail = detail_reactions.get_json()["data"]
    assert len(r_detail["reactions"]) == 2
    usernames = [r["username"] for r in r_detail["reactions"]]
    assert "AuthorUser" in usernames
    assert "ReactorUser" in usernames

    # 9. Toggle off: ReactorUser sends "fire" again to remove reaction
    toggle_res = client.post(f"/api/journals/{post_id}/react", json={
        "type": "fire"
    }, headers=headers2)
    assert toggle_res.status_code == 200
    tog_data = toggle_res.get_json()["data"]
    assert tog_data["action"] == "removed"
    assert tog_data["user_reaction"] is None
    assert tog_data["total_reactions"] == 1
    assert tog_data["reaction_counts"] == {"fire": 1}

    # 10. Delete reaction explicitly for AuthorUser
    del_react = client.delete(f"/api/journals/{post_id}/react", headers=headers1)
    assert del_react.status_code == 200
    del_data = del_react.get_json()["data"]
    assert del_data["user_reaction"] is None
    assert del_data["total_reactions"] == 0
    assert del_data["reaction_counts"] == {}

