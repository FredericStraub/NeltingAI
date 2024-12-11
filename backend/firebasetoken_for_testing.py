import firebase_admin
from firebase_admin import auth, credentials
import requests
from fastapi import HTTPException, status

def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verifies the Firebase ID token and returns the decoded token.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
# Initialize Firebase Admin SDK (if not already initialized)
cred = credentials.Certificate('/Volumes/External/Netling AI/backend/app/serviceAccountKeyFireBase.json')
firebase_admin.initialize_app(cred)

# Sign in using email and password via Firebase REST API
email = 'fred@gmail.com'
password = 'test123'
api_key = 'AIzaSyDPOiSoJkT0g9iSYZYNuXq9C6oUULPJbrY'  # From Firebase project settings

payload = {
    'email': email,
    'password': password,
    'returnSecureToken': True
}

r = requests.post(f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}', json=payload)
id_token = r.json()['idToken']
print(f'ID Token: {id_token}')
print(verify_firebase_id_token(id_token))
