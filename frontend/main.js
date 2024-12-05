// main.js

import { appendMessage, displaySystemMessage, updateMessageContent, repr } from './ui.js';
import { createNewChat, sendChatMessageStream } from './chat.js';
import { getAuthInstance, getFirestoreInstance, firebaseInitializationPromise, logoutUser } from './firebase.js';
import { collection, doc, getDoc } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js';
/**
 * Handle creating a new chat session
 * @returns {Promise<string|null>} - Returns the new chat ID or null on failure
 */
async function handleCreateNewChat() {
  try {
    const newChatId = await createNewChat();
    appendMessage('System', `New chat session started.`);
    console.log(`New chat created: ${newChatId}`); // Debug
    return newChatId;
  } catch (error) {
    console.error("Create New Chat Error:", error);
    alert(`Failed to create a new chat: ${error.message}`);
    return null;
  }
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
  const sendButton = document.getElementById("sendButton");
  const newChatButton = document.getElementById("newChatButton");
  const messageInput = document.getElementById("messageInput");
  const logoutButton = document.getElementById("logoutButton");

  // Handle "New Chat" button click
  newChatButton.addEventListener('click', async () => {
    currentChatId = await handleCreateNewChat();
    console.log(`New Chat ID set to: ${currentChatId}`); // Debug

    // Close any existing EventSource connection
    closeEventSource();
  });

  // Handle "Logout" button click
  logoutButton.addEventListener('click', async () => {
    try {
      await logoutUser();
      console.log('User logged out successfully'); // Debug
      window.location.href = 'login.html'; // Redirect after logout
    } catch (error) {
      console.error("Logout Error:", error);
      alert(`Logout failed: ${error.message}`);
    }
  });

  // Handle sending messages
  sendButton.addEventListener("click", async () => {
    const message = messageInput.textContent.trim();

    if (!currentChatId) {
      alert("No active chat. Please create a new chat.");
      return;
    }

    if (!message) {
      alert("Please enter a message.");
      return;
    }

    // Display user message
    appendMessage("User", message);
    console.log(`User sent message: ${message}`); // Debug
    messageInput.textContent = "";

    // Create a placeholder for the assistant's response
    const assistantMessageElement = appendMessage("Assistant", "");
    console.log('Assistant message element created:', assistantMessageElement); // Debug

    // Close any existing EventSource connection before starting a new one
    closeEventSource();

    // Send message and handle streaming response
    try {
      sendChatMessageStream(
        currentChatId,
        message,
        (data, isFinal) => {
          updateMessageContent(assistantMessageElement, data, isFinal);
          console.log(`Assistant received data chunk: ${repr(data)}`); // Debug
        },
        (error) => {
          updateMessageContent(
            assistantMessageElement,
            `Error: ${error.message || "An unknown error occurred."}`,
            true
          );
          console.error("Assistant Error:", error); // Debug
        }
      );
    } catch (error) {
      updateMessageContent(
        assistantMessageElement,
        `Error: ${error.message || "An unknown error occurred."}`,
        true
      );
      console.error("Send Message Error:", error); // Debug
    }
  });

  // Allow sending message with Enter key and prevent line breaks
  messageInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent inserting a new line
      sendButton.click();
    }
  });

  // Optional: Implement cursor position logic if needed
  messageInput.addEventListener('input', updateCursorPosition);
  messageInput.addEventListener('click', updateCursorPosition);
  messageInput.addEventListener('keyup', updateCursorPosition);
  messageInput.addEventListener('focus', () => {
    updateCursorPosition();
  });
  messageInput.addEventListener('blur', () => {
    // Reset cursor position if needed
    messageInput.style.setProperty('--cursor-x', `0px`);
    messageInput.style.setProperty('--cursor-y', `0px`);
  });
}

/**
 * Update cursor position (if you have custom cursor logic)
 */
function updateCursorPosition() {
  // Your existing cursor position logic
}

/**
 * Initialize authentication state listener
 */
async function initializeAuthListener() {
  // Wait for Firebase initialization to complete
  await firebaseInitializationPromise;
  const authInstance = await getAuthInstance();

  authInstance.onAuthStateChanged(async (user) => {
    if (user) {
      console.log('User is authenticated:', user); // Debug
      // Call checkUserRoleAndUpdateUI here
      await checkUserRoleAndUpdateUI();
      if (!currentChatId) {
        currentChatId = await handleCreateNewChat();
        console.log(`Current Chat ID set to: ${currentChatId}`); // Debug
      }
    } else {
      console.log('User is not authenticated. Redirecting to login.'); // Debug
      // Redirect to login if not authenticated
      window.location.href = 'login.html';
    }
  });
}

async function checkUserRoleAndUpdateUI() {
  // Ensure Firebase is initialized
  await firebaseInitializationPromise;

  const authInstance = await getAuthInstance();
  const user = authInstance.currentUser;

  if (!user) {
    console.error("No user is currently logged in.");
    return;
  }

  const uid = user.uid;

  // Get Firestore instance
  const firestore = await getFirestoreInstance();

  try {
    // Use modular Firestore syntax to reference the user's document
    const userDocRef = doc(collection(firestore, 'user'), uid);
    const userDoc = await getDoc(userDocRef);

    if (!userDoc.exists()) {
      console.error("User document not found in Firestore.");
      return;
    }

    const userData = userDoc.data();
    const role = userData.role || 'user';

    const documentsTab = document.getElementById('documentsTab');
    if (role === 'admin') {
      // Show the 'Documents' tab
      if (documentsTab) {
        documentsTab.style.display = 'block';
      }
    } else {
      // Hide the 'Documents' tab
      if (documentsTab) {
        documentsTab.style.display = 'none';
      }
    }
  } catch (error) {
    console.error("Error fetching user role from Firestore:", error);
  }
}


/**
 * Close the EventSource connection if it exists
 */
function closeEventSource() {
  if (window.currentEventSource) {
    window.currentEventSource.close();
    window.currentEventSource = null;
    console.log('EventSource connection closed.'); // Debug
  }
}

// Global variable to track current chat ID
let currentChatId = null;

// Initialize the application
initializeAuthListener();
initializeEventListeners();