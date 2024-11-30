// ui.js

import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
import DOMPurify from 'https://cdn.jsdelivr.net/npm/dompurify@2.4.0/+esm';

/**
 * Append a message to the chat window
 * @param {string} sender - 'User', 'Assistant', or 'System'
 * @param {string} message - The message content
 * @returns {HTMLElement|null} - The created message element, or null for system messages
 */
function appendMessage(sender, message) {
    if (sender === 'System') {
      displaySystemMessage(message);
      return null;
    }
  
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender.toLowerCase());
  
    // Create and append the sender's name
    const senderElement = document.createElement('strong');
    senderElement.textContent = `${sender}:`;
    messageElement.appendChild(senderElement);
  
    // Create and append the message content
    let contentElement;
    if (sender === 'Assistant') {
      contentElement = document.createElement('div'); // Block-level for Assistant
      contentElement.classList.add('message-content');
      // Add loading indicator
      const loadingElement = document.createElement('span');
      loadingElement.classList.add('message-loading');
      loadingElement.textContent = 'Typing...';
      contentElement.appendChild(loadingElement);
    } else {
      contentElement = document.createElement('span'); // Inline for User
      contentElement.classList.add('message-content');
      contentElement.textContent = message; // Directly set text for user messages
    }
    messageElement.appendChild(contentElement);
  
    const chatWindow = document.getElementById('chatWindow');
    chatWindow.appendChild(messageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the latest message
    return messageElement;
  }

/**
 * Display a system message in the systemMessage container
 * @param {string} message - The system message content
 */
function displaySystemMessage(message) {
  const systemMessage = document.getElementById('systemMessage');
  systemMessage.textContent = message;
  console.log('Displayed system message:', message); // Debug
}

/**
 * Update message content with parsed and sanitized markdown
 * @param {HTMLElement} messageElement - The message element to update
 * @param {string} content - The incoming message content chunk
 * @param {boolean} isFinalChunk - Indicates if this is the final chunk of the message
 */
function updateMessageContent(messageElement, content, isFinalChunk = false) {
    console.log("updateMessageContent called with:", repr(content)); // Debug

    if (!content.trim()) {
        console.log("Empty content received, skipping update.");
        return;
    }

    // Normalize line breaks
    content = content.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

    // Append new chunk to the buffer
    assistantResponseBuffer += content;

    // Format buffer for Markdown
    const formattedBuffer = formatNewlines(assistantResponseBuffer);

    // Select the message content element
    const contentElementDiv = messageElement.querySelector(".message-content");
    if (contentElementDiv) {
        // Remove loading indicator if present
        const loadingElement = contentElementDiv.querySelector(".message-loading");
        if (loadingElement) {
            loadingElement.remove();
            console.log("Removed loading indicator"); // Debug
        }

        try {
            // Parse Markdown into HTML and sanitize
            const dirtyHTML = marked.parse(formattedBuffer);
            const cleanHTML = DOMPurify.sanitize(dirtyHTML);

            // Update the element's content with the formatted response
            contentElementDiv.innerHTML = cleanHTML;
        } catch (error) {
            console.error("Error parsing or updating message content:", error);
        }
    } else {
        console.error("Failed to find .message-content element in messageElement:", messageElement);
    }

    // Scroll to the latest message
    const chatWindow = document.getElementById("chatWindow");
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Reset the buffer if this is the final chunk
    if (isFinalChunk) {
        console.log("Final chunk received. Resetting response buffer.");
        assistantResponseBuffer = '';
    }
}

// Helper function to format newlines
function formatNewlines(text) {
    // Replace carriage returns with newlines
    text = text.replace(/\r/g, '\n');

    // Replace three or more newlines with two newlines (avoid extra empty paragraphs)
    text = text.replace(/\n{3,}/g, '\n\n');

    // Replace single newlines with two spaces and a newline (Markdown line break)
    text = text.replace(/([^\n])\n([^\n])/g, '$1  \n$2');

    return text;
}

let assistantResponseBuffer = ''; // Store accumulated response

/**
 * Reset the assistant response buffer
 */
function resetAssistantResponseBuffer() {
    assistantResponseBuffer = '';
    console.log("Assistant response buffer has been reset.");
}

/**
 * Helper function to visualize escape characters in logs
 * @param {string} str
 * @returns {string}
 */
function repr(str) {
  return str.replace(/\\/g, '\\\\').replace(/\n/g, '\\n');
}

export { appendMessage, displaySystemMessage, updateMessageContent, repr, resetAssistantResponseBuffer };