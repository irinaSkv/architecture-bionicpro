import httpx
import os
import jwt
from typing import Optional, Dict
from jwt import PyJWKClient

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "reports-api")

_jwks_client = None
_jwks_client_error = None

def get_jwks_client():
    global _jwks_client, _jwks_client_error
    if _jwks_client_error:
        raise _jwks_client_error

    if _jwks_client is None:
        jwks_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
        try:
            _jwks_client = PyJWKClient(jwks_url, max_cached_keys=5)
        except Exception as e:
            error_msg = f"Error initializing JWKS client: {e}"
            _jwks_client_error = Exception(error_msg)
            raise _jwks_client_error
    return _jwks_client


async def verify_token(token: str) -> Optional[Dict]:
    try:
        jwks_client = get_jwks_client()

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,
            }

            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options=options,
            )

            return {
                "active": True,
                "username": decoded_token.get("preferred_username") or decoded_token.get("email"),
                "sub": decoded_token.get("sub"),
                "email": decoded_token.get("email"),
                "exp": decoded_token.get("exp"),
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    except Exception:
        return None


async def get_user_info(token: str) -> Optional[Dict]:
    try:
        userinfo_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )

            if response.status_code == 200:
                return response.json()

            return None
    except Exception:
        return None