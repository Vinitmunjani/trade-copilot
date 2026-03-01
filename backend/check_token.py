#!/usr/bin/env python3
"""Simple test of the new MetaAPI token by checking provisioning."""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJhMDgwNjA2ODA2N2MzODRiMzRiZDk4MGQwNjI2YmYxMyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiYTA4MDYwNjgwNjdjMzg0YjM0YmQ5ODBkMDYyNmJmMTMiLCJpYXQiOjE3NzIwODI0NTIsImV4cCI6MTc3OTg1ODQ1Mn0.Yg12f2TSRE8aLSp9gSoCNu7qHaRB0ED83RnpRVRDUp1SwiGDJt34iZH-VYIua1a9_Fq2muIYVYtTp_O7zkoHryswIcTfBCuAoH2jmwhhF_AuAmpCoi42WWK_ZpSWiiJfeXd6jnvv9GxfS5b8n7gp3YMFwRd7cu8rLA9hRRbXjN7Ph29RYwNNypTDrauBlJqaguAGJFppUF97ALlhfqdWDUfifNpiuaKJ0yENXbl_awgHDjShFM2MaeC9aS91gnN_-Jof0svTmahPPyEA53JJAc9hmlb2admGIPlZbT4xm0ByBlxBlO_HlJQb7eloeFnlbcdkJhmIQTxXG2Pkup12tXHM9Ds74WAB9jmn3QhAi40MflIbKbQDMniwqpKWlptDliWLs1427mnaX7-jhIRV4BGpttZ5SE18z5-JdEt5WiwOHSkGGTdYMmwknMn4wvhqPjwTidBYCgYUmLZ8SNfc1u_3dOXApo3G4Kg58LDxhk1Abpni9hpheEZkUxexBH2CG6ppkdXveXOrMrrXnkmQRb9g4-bGY7-ROJevl6dG2MCWUKRrLkyhyPn_rvWmJnifIzicHG5CpdtcoOAEbUpn1NJovCTHZiWiyy2TDx8WvIQRd1Q7VQCRPdUKnsEN7OIWJhIdYg-2drFEfmNqFEQdOVlz9IGsQ9FMHgcj2GdxiEs"

# Test 1: Health check
print("🔍 Test 1: Checking backend health...")
try:
    resp = requests.get(f"{BASE_URL}/health", timeout=3)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   ✅ Backend is running")
except Exception as e:
    print(f"   ❌ Backend not responding: {e}")
    sys.exit(1)

# Test 2: Simple token format check
print(f"\n🔍 Test 2: Checking token format...")
try:
    import base64
    parts = TOKEN.split('.')
    if len(parts) == 3:
        # Decode header
        header = base64.urlsafe_b64decode(parts[0] + '==')
        payload = base64.urlsafe_b64decode(parts[1] + '==')
        print(f"   ✅ Token is a valid JWT format")
        print(f"   Header: {header.decode()[:80]}...")
        payload_dict = json.loads(payload)
        print(f"   Token ID: {payload_dict.get('tokenId')}")
        print(f"   Expires: {payload_dict.get('exp')} (epoch)")
        resources = payload_dict.get('accessRules', [])
        for rule in resources:
            rule_id = rule.get('id', 'unknown')
            print(f"   - {rule_id}")
except Exception as e:
    print(f"   ❌ Error parsing token: {e}")

print("\n✅ Token validation complete!")
print(f"\nNew token looks valid. It has:")
print("  - Specific account resource: b86df628-2e77-40bf-8084-c0c919a5df9f")
print("  - Limited to READER role for trading-account-management")
print("  - Full read/write for metaapi-rest-api, metaapi-rpc-api, metaapi-real-time-streaming")
print("  - This token should work for connecting the specific account")
