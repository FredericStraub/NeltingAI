# backend/app/tests/test_firestore.py

import asyncio
from firebase_admin import credentials, firestore, initialize_app

# Initialize Firebase Admin SDK
cred = credentials.Certificate('backend/app/serviceAccountKeyFireBase.json')  # Ensure this path is correct
initialize_app(cred)

db = firestore.client()

async def test_firestore():
    test_ref = db.collection('test_collection').document('test_doc')
    try:
        await asyncio.get_event_loop().run_in_executor(None, test_ref.set, {
            'created_at': firestore.SERVER_TIMESTAMP,
            'message': 'This is a test message.'
        })
        print("Test document written successfully.")
    except Exception as e:
        print(f"Error writing test document: {e}")

if __name__ == "__main__":
    asyncio.run(test_firestore())
