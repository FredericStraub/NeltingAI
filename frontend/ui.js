// ui.js

import { Parser, HtmlRenderer } from 'https://esm.sh/commonmark@0.30.0';
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

  let contentElement;

  if (sender === 'Assistant') {
    // Create and append the sender's name
    const senderElement = document.createElement('strong');
    senderElement.textContent = `${sender}:`;
    messageElement.appendChild(senderElement);

    contentElement = document.createElement('div'); // Block-level for Assistant
    contentElement.classList.add('message-content');

    // Add loading indicator
    const loadingElement = document.createElement('span');
    loadingElement.classList.add('message-loading');
    loadingElement.textContent = 'Typing...';
    contentElement.appendChild(loadingElement);

    // Initialize assistant response buffer and parser state for this message element
    messageElement.assistantResponseBuffer = '';
    messageElement.parser = new Parser();
    messageElement.renderer = new HtmlRenderer();
  } else if (sender === 'User') {
    // For user messages, we skip adding the sender's name
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

  
  // Normalize line breaks
  content = content.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  // Append new chunk to the buffer
  messageElement.assistantResponseBuffer += content;

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
      // Parse the accumulated buffer incrementally
      const parsed = messageElement.parser.parse(messageElement.assistantResponseBuffer);

      // Render the parsed document
      const dirtyHTML = messageElement.renderer.render(parsed);

      // Sanitize the HTML
      const cleanHTML = DOMPurify.sanitize(dirtyHTML);

      // Update the element's content with the formatted response

  // Update the element's content with the formatted response
      contentElementDiv.innerHTML = cleanHTML;

      // Remove <p> tags inside <li> elements
      const listItemParagraphs = contentElementDiv.querySelectorAll('li > p');
      listItemParagraphs.forEach(paragraph => {
        const parentLi = paragraph.parentElement;
        // Move the content of <p> into <li>
        while (paragraph.firstChild) {
          parentLi.insertBefore(paragraph.firstChild, paragraph);
        }
        // Remove the now-empty <p> tag
        parentLi.removeChild(paragraph);
      });

    } catch (error) {
      console.error("Error parsing or updating message content:", error);
    }
  } else {
    console.error("Failed to find .message-content element in messageElement:", messageElement);
  }

  // Scroll to the latest message
  const chatWindow = document.getElementById("chatWindow");
  chatWindow.scrollTop = chatWindow.scrollHeight;

  if (isFinalChunk) {
    console.log("Final chunk received. Assistant response complete.");
    // Optionally, perform any final actions here
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

export { appendMessage, displaySystemMessage, updateMessageContent, repr };