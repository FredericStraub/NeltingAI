// chat.js

import { getAuthInstance, firebaseInitializationPromise } from './firebase.js';

/**
 * Clear the chat window
 */
function clearChat() {
  const chatWindow = document.getElementById('chatWindow');
  if (chatWindow) {
    chatWindow.innerHTML = ""; // Clear all child elements
    console.log("Chat window cleared.");
  } else {
    console.error("Chat window element not found.");
  }
}

/**
 * Create a new chat session
 * @returns {Promise<string>} - Returns the new chat ID
 */
async function createNewChat() {
  // Ensure Firebase is initialized
  await firebaseInitializationPromise;
  const authInstance = await getAuthInstance();
  const user = authInstance.currentUser;

  if (!user) {
    alert("You must be logged in to create a new chat.");
    return;
  }

  try {
    const endpoint = "http://127.0.0.1:8000/chat/new";

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Include cookies in the request
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Error Data:", errorData);
      throw new Error(errorData.detail || "Failed to create a new chat.");
    }

    const data = await response.json();
    const newChatId = data.chat_id;
    console.log(`Backend returned newChatId: ${newChatId}`); // Debug
    clearChat();
    return newChatId;
  } catch (error) {
    console.error("Create New Chat Error:", error);
    alert(`Failed to create a new chat: ${error.message}`);
    throw error;
  }
}

function sendChatMessageStream(chatId, question, onMessage, onError) {
  // First, send the user's message via POST
  sendUserMessage(chatId, question)
    .then(() => {
      // Start listening to the SSE stream
      startSSE(chatId, onMessage, onError);
    })
    .catch((error) => {
      console.error("Error sending message:", error);
      if (onError) {
        onError(error);
      }
    });
}

async function sendUserMessage(chatId, question) {
  const endpoint = `http://127.0.0.1:8000/chat/${chatId}/message`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
    credentials: 'include', // Include cookies in the request
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText);
  }
}

// chat.js

function startSSE(chatId, onMessage, onError) {
  const endpoint = `http://127.0.0.1:8000/chat/${chatId}/stream`;
  const eventSource = new EventSource(endpoint, { withCredentials: true });

  eventSource.onopen = () => {
    console.log("SSE connection opened.");
  };

  eventSource.onmessage = (event) => {
    console.log("Received SSE data:", event.data); // Debug
    onMessage(event.data, false);
  };

  eventSource.onerror = (err) => {
    console.warn("SSE connection closed by server or network error:", err);

    // Indicate completion to the message handler
    onMessage("", true); // This will set isFinalChunk to true

    // Close the EventSource connection
    eventSource.close();
  };

  window.currentEventSource = eventSource;
}



export { createNewChat, sendChatMessageStream };