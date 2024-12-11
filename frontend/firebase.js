// firebase.js

// Import Firebase modules from CDN
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  signInWithCustomToken,
  signOut,
} from "https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js";

// Initialize Firebase App, Auth, and Firestore instances
let app, auth, firestore;
let firebaseInitializationPromise;

/**
 * Configuration
 */
const API_BASE_URL = 'http://127.0.0.1:8000'; // Backend base URL
const REGISTER_ENDPOINT = '/auth/register'; // Registration endpoint

/**
 * Initialize Firebase by fetching configuration from the backend
 * This allows dynamic configuration without exposing sensitive details in the frontend
 */
function initializeFirebase() {
  firebaseInitializationPromise = fetch(`${API_BASE_URL}/firebase-config`)
    .then(async (response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch Firebase configuration");
      }
      const firebaseConfig = await response.json();
      app = initializeApp(firebaseConfig);
      auth = getAuth(app);
      firestore = getFirestore(app); // Initialize Firestore
      console.log("Firebase initialized:", app);
    })
    .catch((error) => {
      console.error("Firebase initialization error:", error);
    });

  return firebaseInitializationPromise;
}

// Start Firebase initialization upon script load
initializeFirebase();

/**
 * Get the Firebase Auth instance after initialization
 * @returns {Promise<Auth>} Firebase Auth instance
 * @throws Will throw an error if Firebase Auth is not initialized
 */
async function getAuthInstance() {
  await firebaseInitializationPromise;
  if (!auth) {
    throw new Error("Firebase Auth not initialized");
  }
  return auth;
}

/**
 * Get the Firestore instance after initialization
 * @returns {Promise<Firestore>} Firestore instance
 * @throws Will throw an error if Firestore is not initialized
 */
async function getFirestoreInstance() {
  await firebaseInitializationPromise;
  if (!firestore) {
    throw new Error("Firestore not initialized");
  }
  return firestore;
}

/**
 * Register a new user by communicating with the backend
 * The backend handles user creation in Firebase Auth and Firestore,
 * then returns a custom token for frontend authentication
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @param {string} username - User's chosen username
 * @returns {Promise<User>} Authenticated Firebase User object
 * @throws Will throw an error if registration fails
 */
async function signup(email, password, username) {
  try {
    // Send registration data to the backend
    const response = await fetch(`${API_BASE_URL}${REGISTER_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, username }),
    });

    // Handle non-OK responses
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    // Parse the successful response
    const data = await response.json();
    const { access_token, uid, email: userEmail } = data;

    // Ensure Firebase Auth is initialized
    const authInstance = await getAuthInstance();

    // Authenticate the user with the custom token
    const userCredential = await signInWithCustomToken(authInstance, access_token);
    return userCredential.user;
  } catch (error) {
    console.error('Signup Error:', error);
    throw error;
  }
}

/**
 * Log in an existing user using email and password
 * Authenticates with Firebase Auth and communicates the ID token to the backend
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise<User>} Authenticated Firebase User object
 * @throws Will throw an error if login fails
 */
async function login(email, password) {
  try {
    const authInstance = await getAuthInstance();
    const userCredential = await signInWithEmailAndPassword(authInstance, email, password);
    const user = userCredential.user;

    // Retrieve the ID token for backend verification
    const idToken = await user.getIdToken();

    // Send the ID token to the backend to set HTTP-only cookies or perform other actions
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
 * Log out the current user from Firebase Auth and inform the backend to clear authentication cookies
 * 
 * @returns {Promise<void>}
 * @throws Will throw an error if logout fails
 */
async function logoutUser() {
  try {
    const authInstance = await getAuthInstance();

    // Sign out from Firebase Auth
    await signOut(authInstance);

    // Inform the backend to clear the authentication cookie
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: "include", // Include cookies in request
    });
  } catch (error) {
    console.error("Logout Error:", error);
    throw error;
  }
}

// Export additional helper functions and promises
export {
  getAuthInstance,
  getFirestoreInstance,
  firebaseInitializationPromise,
  signup,
  login,
  logoutUser,
};