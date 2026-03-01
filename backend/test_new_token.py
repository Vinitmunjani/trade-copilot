#!/usr/bin/env python3
"""Test the new MetaAPI token by attempting account provisioning."""

import httpx
import asyncio
import sys
from app.core.security import create_access_token, hash_password
from app.database import async_session_factory, init_db
from app.models.user import User
from sqlalchemy import select

BASE_URL = "http://localhost:8000"

async def create_test_user():
    """Create or get test user."""
    await init_db()
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == 'test_trader@example.com'))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email='test_trader@example.com', hashed_password=hash_password('password'))
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

async def test_account_connection():
    """Test account connection with new token."""
    
    # Create test user
    print("📝 Creating test user...")
    user = await create_test_user()
    user_id = str(user.id)
    print(f"✅ User created: {user_id}")
    
    # Generate token
    token = create_access_token({'sub': user_id})
    
    # Test registration
    print("\n🔐 Testing user registration...")
    async with httpx.AsyncClient() as client:
        reg_resp = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": f"reg_test_{user_id}@example.com", "password": "testpass123"}
        )
        print(f"Registration: {reg_resp.status_code}")
        if reg_resp.status_code == 201:
            reg_data = reg_resp.json()
            token = reg_data.get('access_token')
            print(f"✅ New token generated: {token[:50]}...")
        else:
            print(f"Response: {reg_resp.text}")
    
    # Test account connection with new token
    print("\n🔗 Testing account connection with new token...")
    new_token = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJhMDgwNjA2ODA2N2MzODRiMzRiZDk4MGQwNjI2YmYxMyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiYTA4MDYwNjgwNjdjMzg0YjM0YmQ5ODBkMDYyNmJmMTMiLCJpYXQiOjE3NzIwODI0NTIsImV4cCI6MTc3OTg1ODQ1Mn0.Yg12f2TSRE8aLSp9gSoCNu7qHaRB0ED83RnpRVRDUp1SwiGDJt34iZH-VYIua1a9_Fq2muIYVYtTp_O7zkoHryswIcTfBCuAoH2jmwhhF_AuAmpCoi42WWK_ZpSWiiJfeXd6jnvv9GxfS5b8n7gp3YMFwRd7cu8rLA9hRRbXjN7Ph29RYwNNypTDrauBlJqaguAGJFppUF97ALlhfqdWDUfifNpiuaKJ0yENXbl_awgHDjShFM2MaeC9aS91gnN_-Jof0svTmahPPyEA53JJAc9hmlb2admGIPlZbT4xm0ByBlxBlO_HlJQb7eloeFnlbcdkJhmIQTxXG2Pkup12tXHM9Ds74WAB9jmn3QhAi40MflIbKbQDMniwqpKWlptDliWLs1427mnaX7-jhIRV4BGpttZ5SE18z5-JdEt5WiwOHSkGGTdYMmwknMn4wvhqPjwTidBYCgYUmLZ8SNfc1u_3dOXApo3G4Kg58LDxhk1Abpni9hpheEZkUxexBH2CG6ppkdXveXOrMrrXnkmQRb9g4-bGY7-ROJevl6dG2MCWUKRrLkyhyPn_rvWmJnifIzicHG5CpdtcoOAEbUpn1NJovCTHZiWiyy2TDx8WvIQRd1Q7VQCRPdUKnsEN7OIWJhIdYg-2drFEfmNqFEQdOVlz9IGsQ9FMHgcj2GdxiEs"
    
    async with httpx.AsyncClient() as client:
        connect_resp = await client.post(
            f"{BASE_URL}/api/v1/account/connect",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "login": 19023151,
                "password": "Y3xL4eW2p9",
                "server": "Exness-MT5Trial8",
                "metaapi_token": new_token
            }
        )
        print(f"Connect Status: {connect_resp.status_code}")
        print(f"Connect Response: {connect_resp.text[:500]}")
        
        if connect_resp.status_code == 200:
            print("✅ Account connected successfully!")
            data = connect_resp.json()
            print(f"Account: {data}")
        else:
            print(f"❌ Failed to connect account")
            if "authentication" in connect_resp.text.lower():
                print("🔑 Issue: MetaAPI authentication failed")
            elif "already" in connect_resp.text.lower():
                print("⚠️  Issue: Account already connected")

if __name__ == "__main__":
    asyncio.run(test_account_connection())
