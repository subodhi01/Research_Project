import os
import hashlib

from ..database import SessionLocal
from ..models import User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


SEED_USERS = [
    {
        "username": "alice",
        "full_name": "Alice Johnson",
        "email": "alice@example.com",
        "department": "Dev",
        "role": "Engineer",
    },
    {
        "username": "bob",
        "full_name": "Bob Smith",
        "email": "bob@example.com",
        "department": "Dev",
        "role": "Engineer",
    },
    {
        "username": "carol",
        "full_name": "Carol Lee",
        "email": "carol@example.com",
        "department": "IT",
        "role": "Admin",
    },
    {
        "username": "dave",
        "full_name": "Dave Martinez",
        "email": "dave@example.com",
        "department": "IT",
        "role": "Analyst",
    },
    {
        "username": "erin",
        "full_name": "Erin Patel",
        "email": "erin@example.com",
        "department": "HR",
        "role": "Manager",
    },
    {
        "username": "frank",
        "full_name": "Frank Wright",
        "email": "frank@example.com",
        "department": "HR",
        "role": "Specialist",
    },
    {
        "username": "grace",
        "full_name": "Grace Kim",
        "email": "grace@example.com",
        "department": "Management",
        "role": "Director",
    },
    {
        "username": "heidi",
        "full_name": "Heidi Chen",
        "email": "heidi@example.com",
        "department": "Management",
        "role": "VP",
    },
    {
        "username": "ivan",
        "full_name": "Ivan Petrov",
        "email": "ivan@example.com",
        "department": "Dev",
        "role": "Engineer",
    },
    {
        "username": "judy",
        "full_name": "Judy Brown",
        "email": "judy@example.com",
        "department": "IT",
        "role": "Engineer",
    },
    {
        "username": "mallory",
        "full_name": "Mallory Davis",
        "email": "mallory@example.com",
        "department": "Security",
        "role": "Analyst",
    },
    {
        "username": "oscar",
        "full_name": "Oscar Ruiz",
        "email": "oscar@example.com",
        "department": "Security",
        "role": "Engineer",
    },
]


def main() -> None:
    session = SessionLocal()
    try:
        existing = {u.username for u in session.query(User).all()}
        for data in SEED_USERS:
            if data["username"] in existing:
                existing_user = session.query(User).filter(User.username == data["username"]).first()
                if existing_user and not existing_user.password_hash:
                    existing_user.password_hash = hash_password("password123")
                continue
            user = User(
                username=data["username"],
                password_hash=hash_password("password123"),
                full_name=data["full_name"],
                email=data["email"],
                department=data["department"],
                role=data["role"],
            )
            session.add(user)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()


