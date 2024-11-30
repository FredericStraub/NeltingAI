// firebase.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";

let app, auth;

/**
 * Initialize Firebase dynamically by fetching configuration from the backend
 */
async function initializeFirebase() {
  try {
    const response = await fetch("http://127.0.0.1:8000/firebase-config");
    if (!response.ok) {
      throw new Error("Failed to fetch Firebase configuration");
    }
    const firebaseConfig = await response.json();

    // Initialize Firebase with fetched config
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    console.log('Firebase initialized:', app);
  } catch (error) {
    console.error("Firebase initialization error:", error);
  }
}

await initializeFirebase();

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

    // After successful registration, sign in the user via Firebase Auth
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
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
async function logoutUser() { // Renamed to avoid conflict with 'logout' variable
  try {
    await signOut(auth);
  } catch (error) {
    console.error("Logout Error:", error);
    throw error;
  }
}

export { auth, signup, login, logoutUser };