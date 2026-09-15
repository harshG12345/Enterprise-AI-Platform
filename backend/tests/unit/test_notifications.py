"""Unit tests for Notifications REST API and Service."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notification_full_lifecycle(async_client: AsyncClient):
    """Test full notification lifecycle: creation, listing, read updates, deletion."""
    # 1. Register and authenticate user
    user_email = "notifier@enterprise.ai"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "SecurePassword123!",
            "full_name": "Notification Tester",
            "role": "DATA_SCIENTIST",
        },
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        data={"username": user_email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial unread count (should be 0)
    unread_res = await async_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["data"]["unread_count"] == 0

    # 3. Create a notification
    create_payload = {
        "title": "Model Training Finished",
        "message": "Random Forest model training finished with 89.2% accuracy.",
        "type": "SUCCESS",
        "category": "TRAINING",
        "link": "/models",
    }
    create_res = await async_client.post("/api/v1/notifications", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    created_notif = create_res.json()["data"]
    notif_id = created_notif["id"]
    assert created_notif["title"] == create_payload["title"]
    assert created_notif["is_read"] is False

    # 4. Check unread count (should now be 1)
    unread_res2 = await async_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res2.status_code == 200
    assert unread_res2.json()["data"]["unread_count"] == 1

    # 5. List notifications
    list_res = await async_client.get("/api/v1/notifications", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()["data"]
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert len(data["items"]) == 1

    # 6. Mark single notification as read
    read_res = await async_client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["data"]["is_read"] is True

    # 7. Check unread count (should now be 0)
    unread_res3 = await async_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res3.json()["data"]["unread_count"] == 0

    # 8. Delete notification
    del_res = await async_client.delete(f"/api/v1/notifications/{notif_id}", headers=headers)
    assert del_res.status_code == 200

    # 9. Verify list is now empty
    list_res2 = await async_client.get("/api/v1/notifications", headers=headers)
    assert list_res2.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_notification_batch_actions_and_filtering(async_client: AsyncClient):
    """Test category filtering, unread-only filtering, and bulk mark-all-read."""
    # 1. Register & login
    user_email = "batch_notif@enterprise.ai"
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "SecurePassword123!",
            "full_name": "Batch Tester",
            "role": "DATA_SCIENTIST",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        data={"username": user_email, "password": "SecurePassword123!"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed demo notifications (creates 5 notifications)
    seed_res = await async_client.post("/api/v1/notifications/seed-demo", headers=headers)
    assert seed_res.status_code == 201
    seeded_items = seed_res.json()["data"]
    assert len(seeded_items) == 5

    # 3. Verify unread count is 5
    unread_res = await async_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res.json()["data"]["unread_count"] == 5

    # 4. Filter by DRIFT category
    drift_res = await async_client.get("/api/v1/notifications?category=DRIFT", headers=headers)
    assert drift_res.status_code == 200
    drift_data = drift_res.json()["data"]
    assert drift_data["total"] >= 1
    for item in drift_data["items"]:
        assert item["category"] == "DRIFT"

    # 5. Filter by TRAINING category
    train_res = await async_client.get("/api/v1/notifications?category=TRAINING", headers=headers)
    assert train_res.status_code == 200
    assert train_res.json()["data"]["total"] >= 1

    # 6. Mark all as read
    mark_all_res = await async_client.post("/api/v1/notifications/mark-all-read", headers=headers)
    assert mark_all_res.status_code == 200
    assert mark_all_res.json()["data"]["affected_count"] == 5

    # 7. Verify unread count is now 0
    unread_res2 = await async_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res2.json()["data"]["unread_count"] == 0

    # 8. Clear all notifications
    clear_res = await async_client.delete("/api/v1/notifications", headers=headers)
    assert clear_res.status_code == 200
    assert clear_res.json()["data"]["affected_count"] == 5

    # 9. Verify list is now empty
    list_res = await async_client.get("/api/v1/notifications", headers=headers)
    assert list_res.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_notification_tenant_isolation(async_client: AsyncClient):
    """Ensure User A cannot view, read, or delete User B's notifications."""
    # Register User A
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a@enterprise.ai",
            "password": "SecurePassword123!",
            "full_name": "User A",
            "role": "DATA_SCIENTIST",
        },
    )
    login_a = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "user_a@enterprise.ai", "password": "SecurePassword123!"},
    )
    token_a = login_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b@enterprise.ai",
            "password": "SecurePassword123!",
            "full_name": "User B",
            "role": "DATA_SCIENTIST",
        },
    )
    login_b = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "user_b@enterprise.ai", "password": "SecurePassword123!"},
    )
    token_b = login_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a private notification
    create_res = await async_client.post(
        "/api/v1/notifications",
        json={
            "title": "User A Private Alert",
            "message": "Sensitive training details for User A",
            "type": "INFO",
            "category": "SYSTEM",
        },
        headers=headers_a,
    )
    notif_id = create_res.json()["data"]["id"]

    # User B lists notifications (should not see User A's notification)
    list_b = await async_client.get("/api/v1/notifications", headers=headers_b)
    assert list_b.json()["data"]["total"] == 0

    # User B attempts to mark User A's notification as read (must be forbidden 403)
    read_attempt = await async_client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers_b)
    assert read_attempt.status_code == 403

    # User B attempts to delete User A's notification (must be forbidden 403)
    del_attempt = await async_client.delete(f"/api/v1/notifications/{notif_id}", headers=headers_b)
    assert del_attempt.status_code == 403
