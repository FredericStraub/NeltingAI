# export.py

import os
import json
import asyncio
from datetime import timezone
from app.config import settings
from firebase_admin import credentials, firestore, initialize_app
import logging

logger = logging.getLogger(__name__)

def initialize_export_firebase():
    try:
        cred = credentials.Certificate(settings.SERVICE_ACCOUNT_KEY_PATH)
        initialize_app(cred)
        firestore_client = firestore.client()
        logger.info("Firebase Admin initialized for export.")
        return firestore_client
    except Exception as e:
        logger.exception(f"Failed to initialize Firebase Admin for export: {e}")
        raise e

async def export_chats(export_dir=settings.EXPORT_DIR, iso_format=True):
    print('Exporting chats to JSON')
    file_path = os.path.join(export_dir, 'chats.json')
    firestore_client = initialize_export_firebase()
    chats_ref = firestore_client.collection('chats')  # Ensure 'chats' is lowercase
    chats = []

    try:
        docs = chats_ref.stream()
        for chat_doc in docs:
            chat_data = chat_doc.to_dict()
            if iso_format:
                # Assuming 'created_at' is a Firestore Timestamp
                if 'created_at' in chat_data and chat_data['created_at']:
                    chat_data['created_at'] = chat_data['created_at'].replace(tzinfo=timezone.utc).isoformat()
                for message in chat_data.get('messages', []):
                    if 'created_at' in message and message['created_at']:
                        message['created_at'] = message['created_at'].replace(tzinfo=timezone.utc).isoformat()
            chats.append(chat_data)

        with open(file_path, 'w') as file:
            json.dump(chats, file, indent=2)
        print(f'{len(chats)} chats exported to {file_path}')

    except Exception as e:
        logger.error(f"Failed to export chats: {e}")
        raise e

def main():
    asyncio.run(export_chats())

if __name__ == '__main__':
    main()
