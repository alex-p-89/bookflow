import pytest
from sqlalchemy import select

from src.authorization import AuthorizationModule
from src.main import app
from src.models import UserModel
from src.schemas import (
    BookCreateSchema,
    BookResponseSchema,
    UserRegisterSchema,
    UserResponseSchema,
)


@pytest.mark.asyncio
async def test_register_same_user_twice(client, db_session):
    new_user = UserRegisterSchema(
        username="test user",
        email="test@email.com",
        password="test password"
    )
    # Expecting successful user creation
    response = await client.post("/auth/register", json=new_user.model_dump(mode="json"))
    assert response.status_code == 200, response.json()
    data = UserResponseSchema.model_validate(response.json())
    assert data.user_id is not None

    # Expecting failure because user exists
    response = await client.post("/auth/register", json=new_user.model_dump(mode="json"))
    assert response.status_code != 200, response.json() 
    
    # Expecting only 1 user created in DB
    query = select(UserModel)
    db_users = (await db_session.scalars(query)).all()
    assert len(db_users) == 1


@pytest.mark.asyncio
async def test_login_user(client, db_session):
    non_existent_user_data = {"username": "testuser", "password": "secret"}

    # Expecting failure because there is no user in DB
    response = await client.post("/auth/login", data=non_existent_user_data)
    assert response.status_code != 200, response.json()

    new_user = UserRegisterSchema(
        username=non_existent_user_data["username"],
        email="test@email.com",
        password=non_existent_user_data["password"]
    )

    # Register user
    response = await client.post("/auth/register", json=new_user.model_dump(mode="json"))
    assert response.status_code == 200, response.json()

    # and login him, expecting success
    response = await client.post("/auth/login", data=non_existent_user_data)
    assert response.status_code == 200, response.json()

@pytest.mark.asyncio
async def test_add_book(client, db_session):
    new_book = BookCreateSchema(
        title="test title",
        author="test author",
        published="2026",
        genre="test genre",
        description="test description"
    )

    # Expecting failure because unauthorized users cannot add books
    response = await client.post("/books/", json=new_book.model_dump(mode="json"))
    assert response.status_code != 200, response.json()

    new_user = UserRegisterSchema(
        username="test user",
        email="test@email.com",
        password="test password"
    )

    # Register user
    response = await client.post("/auth/register", json=new_user.model_dump(mode="json"))
    assert response.status_code == 200, response.json()
    user_data = UserResponseSchema.model_validate(response.json())
    # Login him
    response = await client.post(
        "/auth/login", 
        data={"username": new_user.username, "password": new_user.password}
    )
    assert response.status_code == 200, response.json()

    # Get user id
    authorized_user = UserModel(user_id=user_data.user_id)

    async def override_get_current_user():
        yield authorized_user

    # And override authorization dependency for him
    app.dependency_overrides[AuthorizationModule.get_current_user] = override_get_current_user

    # Now expecting succesful book add
    response = await client.post("/books/", json=new_book.model_dump(mode="json"))
    assert response.status_code == 200, response.text
    book_data = BookResponseSchema.model_validate(response.json())
    assert book_data.book_id is not None
    assert book_data.owner_id is not None
    assert book_data.owner_id == authorized_user.user_id

    app.dependency_overrides.clear()






