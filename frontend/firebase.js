// frontend/firebase.js

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
import { 
  getAuth, 
  createUserWithEmailAndPassword, 
  updateProfile, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged, 
  getIdToken 
} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDPOiSoJkT0g9iSYZYNuXq9C6oUULPJbrY",
  authDomain: "neltingairag-27e31.firebaseapp.com",
  projectId: "neltingairag-27e31",
  storageBucket: "neltingairag-27e31.firebasestorage.app",
  messagingSenderId: "473469555546",
  appId: "1:473469555546:web:5273d1f9683800cab11963",
  measurementId: "G-Q93XGQB5QH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

/**
 * Sign up a new user
 * @param {string} email 
 * @param {string} password 
 * @param {string} username 
 * @returns {Promise<User>}
 */
async function signup(email, password, username) {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(userCredential.user, { displayName: username });
    return userCredential.user;
  } catch (error) {
    console.error("Signup Error:", error);
    throw error;
  }
}

/**
 * Log in an existing user
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<User>}
 */
async function login(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return userCredential.user;
  } catch (error) {
    console.error("Login Error:", error);
    throw error;
  }
}

/**
 * Log out the current user
 * @returns {Promise<void>}
 */
async function logout() {
  try {
    await signOut(auth);
  } catch (error) {
    console.error("Logout Error:", error);
    throw error;
  }
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
        // "Content-Type": "application/json" // Not needed if no body is sent
      }
      // No body is sent
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Error Data:", errorData);
      throw new Error(errorData.detail || "Failed to create a new chat.");
    }

    const data = await response.json();
    const newChatId = data.chat_id;
    return newChatId;
  } catch (error) {
    console.error("Create New Chat Error:", error);
    alert(`Failed to create a new chat: ${error.message}`);
    throw error; // Re-throw to allow upstream handling if necessary
  }
}

/**
 * Send a chat message and handle server-sent event response
 * @param {string} chatId 
 * @param {string} question 
 * @param {function} onMessage - Callback to handle incoming message chunks
 * @param {function} onError - Callback to handle errors
 * @returns {Promise<void>}
 */
async function sendChatMessageStream(chatId, question, onMessage, onError) {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User is not authenticated.");
  }

  try {
    const token = await getIdToken(user);
    const endpoint = `http://127.0.0.1:8000/chat/${chatId}`;
    
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question })
    });

    if (!response.ok) {
      const errorData = await response.json();
      const errorMessage = Array.isArray(errorData.detail) 
        ? errorData.detail.map(err => err.msg).join(', ')
        : errorData.detail;
      throw new Error(errorMessage || "Request failed.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let doneReading = false;

    while (!doneReading) {
      const { done, value } = await reader.read();
      if (done) {
        doneReading = true;
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      onMessage(chunk); // Invoke callback with the received chunk
    }
  } catch (error) {
    console.error("Chat Message Stream Error:", error);
    onError(error);
  }
}

// Export functions and Firebase auth instance
export { auth, signup, login, logout, createNewChat, sendChatMessageStream };
