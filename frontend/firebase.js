// firebase.js

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  signInWithCustomToken,
  signOut,
} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";

let app, auth;
let firebaseInitializationPromise;

/**
 * Initialize Firebase dynamically by fetching configuration from the backend
 */
function initializeFirebase() {
  firebaseInitializationPromise = fetch("http://127.0.0.1:8000/firebase-config")
    .then(async (response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch Firebase configuration");
      }
      const firebaseConfig = await response.json();
      app = initializeApp(firebaseConfig);
      auth = getAuth(app);
      console.log("Firebase initialized:", app);
    })
    .catch((error) => {
      console.error("Firebase initialization error:", error);
    });

  return firebaseInitializationPromise;
}

// Start initialization
initializeFirebase();

/**
 * Get the Firebase Auth instance after initialization
 * @returns {Promise<Auth>}
 */
async function getAuthInstance() {
  await firebaseInitializationPromise;
  if (!auth) {
    throw new Error("Firebase Auth not initialized");
  }
  return auth;
}

/**
 * Sign up a new user via the backend
 * @param {string} email
 * @param {string} password
 * @param {string} username
 * @returns {Promise<User>}
 */
async function signup(email, password, username) {
  try {
    // Send registration data to the backend
    const response = await fetch("http://127.0.0.1:8000/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password, username }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed.");
    }

    // Get the custom token from the backend
    const data = await response.json();
    const customToken = data.customToken;

    // Initialize Firebase Auth if not already initialized
    const authInstance = await getAuthInstance();

    // Sign in with the custom token
    const userCredential = await signInWithCustomToken(authInstance, customToken);

    return userCredential.user;
  } catch (error) {
    console.error("Signup Error:", error);
    alert(`Registration failed: ${error.message}`);
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
    const authInstance = await getAuthInstance();
    const userCredential = await signInWithEmailAndPassword(authInstance, email, password);
    const user = userCredential.user;

    // Get the ID token
    const idToken = await user.getIdToken();

    // Send the ID token to the backend /login endpoint
    const response = await fetch("http://127.0.0.1:8000/auth/login", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${idToken}`,
      },
      credentials: "include", // Include cookies in requests
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to log in.");
    }

    return user;
  } catch (error) {
    console.error("Login Error:", error);
    throw error;
  }
}

/**
 * Log out the current user
 * @returns {Promise<void>}
 */
async function logoutUser() {
  try {
    const authInstance = await getAuthInstance();

    // Sign out from Firebase Auth
    await signOut(authInstance);

    // Inform the backend to clear the authentication cookie
    await fetch("http://127.0.0.1:8000/auth/logout", {
      method: "POST",
      credentials: "include", // Include cookies in request
    });
  } catch (error) {
    console.error("Logout Error:", error);
    throw error;
  }
}

export {
  getAuthInstance,
  firebaseInitializationPromise,
  signup,
  login,
  logoutUser,
};