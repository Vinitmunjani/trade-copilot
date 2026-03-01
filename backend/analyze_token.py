#!/usr/bin/env python3
"""Analyze the new MetaAPI token provided by the user."""

import json
import base64

TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJhMDgwNjA2ODA2N2MzODRiMzRiZDk4MGQwNjI2YmYxMyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiYTA4MDYwNjgwNjdjMzg0YjM0YmQ5ODBkMDYyNmJmMTMiLCJpYXQiOjE3NzIwODI0NTIsImV4cCI6MTc3OTg1ODQ1Mn0.Yg12f2TSRE8aLSp9gSoCNu7qHaRB0ED83RnpRVRDUp1SwiGDJt34iZH-VYIua1a9_Fq2muIYVYtTp_O7zkoHryswIcTfBCuAoH2jmwhhF_AuAmpCoi42WWK_ZpSWiiJfeXd6jnvv9GxfS5b8n7gp3YMFwRd7cu8rLA9hRRbXjN7Ph29RYwNNypTDrauBlJqaguAGJFppUF97ALlhfqdWDUfifNpiuaKJ0yENXbl_awgHDjShFM2MaeC9aS91gnN_-Jof0svTmahPPyEA53JJAc9hmlb2admGIPlZbT4xm0ByBlxBlO_HlJQb7eloeFnlbcdkJhmIQTxXG2Pkup12tXHM9Ds74WAB9jmn3QhAi40MflIbKbQDMniwqpKWlptDliWLs1427mnaX7-jhIRV4BGpttZ5SE18z5-JdEt5WiwOHSkGGTdYMmwknMn4wvhqPjwTidBYCgYUmLZ8SNfc1u_3dOXApo3G4Kg58LDxhk1Abpni9hpheEZkUxexBH2CG6ppkdXveXOrMrrXnkmQRb9g4-bGY7-ROJevl6dG2MCWUKRrLkyhyPn_rvWmJnifIzicHG5CpdtcoOAEbUpn1NJovCTHZiWiyy2TDx8WvIQRd1Q7VQCRPdUKnsEN7OIWJhIdYg-2drFEfmNqFEQdOVlz9IGsQ9FMHgcj2GdxiEs"

def analyze():
    try:
        parts = TOKEN.split('.')
        if len(parts) != 3:
            print("❌ Invalid JWT format")
            return
        
        # Decode payload
        payload_data = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_data) % 4
        if padding != 4:
            payload_data += '=' * padding
        
        payload = json.loads(base64.urlsafe_b64decode(payload_data))
        
        print("=" * 70)
        print("📋 METAAPI TOKEN ANALYSIS")
        print("=" * 70)
        
        print(f"\n✅ Token Format: Valid JWT (RSA512)")
        print(f"\n📊 Token Metadata:")
        print(f"   - Token ID: {payload.get('tokenId', 'N/A')}")
        print(f"   - Real User ID: {payload.get('realUserId', 'N/A')[:16]}...")
        print(f"   - Issued: {payload.get('iat')} (epoch)")
        print(f"   - Expires: {payload.get('exp')} (epoch)")
        print(f"   - Impersonated: {payload.get('impersonated', False)}")
        
        print(f"\n🔑 Access Rules:")
        for i, rule in enumerate(payload.get('accessRules', []), 1):
            print(f"\n   Rule {i}: {rule.get('id')}")
            print(f"      Roles: {', '.join(rule.get('roles', []))}")
            
            # Parse resources
            resources = rule.get('resources', [])
            if resources:
                for resource in resources:
                    print(f"      Resource: {resource}")
            
            methods = rule.get('methods', [])
            if methods:
                for method in methods[:2]:  # Show first 2
                    print(f"      Method: {method}")
        
        print(f"\n💡 KEY FINDING:")
        print(f"   This token is BOUND to a SPECIFIC account:")
        print(f"   Account ID: b86df628-2e77-40bf-8084-c0c919a5df9f")
        print(f"\n   This is DIFFERENT from the previous token which had:")
        print(f"   - Full wildcard access (*) to all accounts under the user")
        print(f"   - Writer role for trading-account-management-api")
        print(f"\n   This token RESTRICTS access to ONE specific account only!")
        
        print(f"\n⚠️  POSSIBLE ISSUE:")
        print(f"   The previous token worked (at least syntactically) because it had")
        print(f"   wildcards and higher permissions. This new token is more restrictive.")
        print(f"   It's bound to account: b86df628-2e77-40bf-8084-c0c919a5df9f")
        print(f"\n   For the account provisioning to work, we need to verify:")
        print(f"   1. Does this token's account ID match your MT5 account setup in MetaAPI?")
        print(f"   2. Is the MT5 account (login: 19023151) provisioned under this account?")
        
        print(f"\n📌 RECOMMENDATION:")
        print(f"   Option A: Get a token with full write access (like the first one)")
        print(f"   Option B: Ensure the MT5 login 19023151 is under account")
        print(f"             b86df628-2e77-40bf-8084-c0c919a5df9f in MetaAPI")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze()
