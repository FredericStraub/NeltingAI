// chat.js

import { auth } from './firebase.js';
import { resetAssistantResponseBuffer } from './ui.js'; // Import the reset function

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

    // Reset the response buffer in ui.js
    resetAssistantResponseBuffer();
    console.log("Assistant response buffer reset.");
}

/**
 * Create a new chat session
 * @returns {Promise<string>} - Returns the new chat ID
 */
async function createNewChat() {
  const user = auth.currentUser;
  if (!user) {
    alert("You must be logged in to create a new chat.");
    return;
  }

  try {
    const token = await user.getIdToken();
    const endpoint = "http://127.0.0.1:8000/chat/new";

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      }
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

/**
 * Send a chat message and handle streaming response
 * @param {string} chatId
 * @param {string} question
 * @param {function} onMessage - Callback to handle incoming message chunks
 * @param {function} onError - Callback to handle errors
 * @returns {Promise<void>}
 */
async function sendChatMessageStream(chatId, question, onMessage, onError) {
  const user = auth.currentUser;
  if (!user) {
      console.error("User is not authenticated.");
      return;
  }

  try {
      const token = await user.getIdToken();
      const endpoint = `http://127.0.0.1:8000/chat/${chatId}`;

      const response = await fetch(endpoint, {
          method: "POST",
          headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
              Accept: "text/event-stream",
          },
          body: JSON.stringify({ question }),
      });

      if (!response.ok) {
          const errorText = await response.text();
          console.error("Server error response:", errorText);
          onError(new Error(errorText));
          return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        console.log("Buffer:", repr(buffer))

        const events = buffer.split("\r\n\r\n");
        console.log("Buffer after split:", repr(buffer))

        buffer = events.pop(); // Retain incomplete message

        for (const event of events) {
            const lines = event.trim().split("\r\n");
            for (const line of lines) {
                if (line.startsWith("data:")) {
                    const data = line.substring(6);
                    onMessage(data, false);
                    
                }
            }
        }
    }
    onMessage('', true);
  } catch (error) {
      console.error("Stream processing error:", error);
      onError(error);
  }
}

/**
 * Helper function to visualize escape characters in logs
 * @param {string} str
 * @returns {string}
 */
function repr(str) {
  return str.replace(/\\/g, '\\\\').replace(/\n/g, '\\n');
}

export { createNewChat, sendChatMessageStream };