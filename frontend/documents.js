// Configuration
const API_BASE_URL = 'http://127.0.0.1:8000'; // Adjust as necessary
const DOCUMENTS_ENDPOINT = '/api/documents'; // Endpoint to fetch documents
const UPLOAD_ENDPOINT = '/upload/upload-file/'; // Endpoint to upload files
const LOGOUT_ENDPOINT = '/auth/logout'; // Endpoint to handle logout

// DOM Elements
const documentsContainer = document.getElementById('documentsContainer');
const logoutButton = document.getElementById('logoutButton');
const uploadButton = document.getElementById('uploadButton');
const fileInput = document.getElementById('fileInput');

// Import Firebase and Firestore utilities
import { logoutUser, getAuthInstance, firebaseInitializationPromise, getFirestoreInstance } from './firebase.js';
import { collection, doc, getDoc } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js';


async function initializeAuthListener() {
    // Wait for Firebase initialization to complete
    await firebaseInitializationPromise;
    const authInstance = await getAuthInstance();
  
    authInstance.onAuthStateChanged(async (user) => {
      if (user) {
        console.log('User is authenticated:', user); // Debug
        // Call checkAdminAccess and pass the user
        await checkAdminAccess(user);
      } else {
        console.log('User is not authenticated. Redirecting to login.'); // Debug
        // Redirect to login if not authenticated
        window.location.href = 'login.html';
      }
    });
  }
// Check Admin Access
async function checkAdminAccess(user) {
    // Ensure Firebase is initialized
    await firebaseInitializationPromise;
  
    if (!user) {
      console.error("No user is currently logged in.");
      window.location.href = 'login.html';
      return;
    }
  
    const uid = user.uid;
    const firestore = await getFirestoreInstance();
  
    try {
      const userDocRef = doc(collection(firestore, 'user'), uid);
      const userDoc = await getDoc(userDocRef);
  
      if (!userDoc.exists()) {
        console.error("User document not found in Firestore.");
        window.location.href = 'login.html';
        return;
      }
  
      const userData = userDoc.data();
      const role = userData.role || 'user';
  
      if (role !== 'admin') {
        alert("You do not have permission to access this page.");
        window.location.href = 'chat.html';
      } else {
        console.log("User is admin. Proceeding to load documents.");
        await fetchAndRenderDocuments();
      }
    } catch (error) {
      console.error("Error fetching user role from Firestore:", error);
    }
  }

// Fetch and Render Documents
async function fetchAndRenderDocuments() {
  try {
    documentsContainer.innerHTML = '<p>Loading documents...</p>';

    const response = await fetch(`${API_BASE_URL}${DOCUMENTS_ENDPOINT}`, {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized. Please log in.');
      }
      throw new Error(`Error fetching documents: ${response.statusText}`);
    }

    const data = await response.json();
    documentsContainer.innerHTML = '';

    if (data.length === 0) {
      documentsContainer.innerHTML = '<p>No documents found.</p>';
      return;
    }

    // Render documents
    data.forEach((doc) => {
      const section = document.createElement('section');
      section.classList.add('document-section');

      section.innerHTML = `
        <h3 class="document-title">${doc.file_name || 'Unnamed Document'}</h3>
        <p class="document-description">${doc.description || 'No Description'}</p>
        <p class="document-type"><strong>Type:</strong> ${doc.file_type || 'Unknown'}</p>
        <p class="document-size"><strong>Size:</strong> ${formatBytes(doc.size)}</p>
        <p class="document-uploaded-at"><strong>Uploaded At:</strong> ${new Date(doc.uploaded_at.seconds * 1000).toLocaleString()}</p>
        <a href="${doc.file_url || '#'}" target="_blank" rel="noopener noreferrer" class="document-link">View Document</a>
        <button class="delete-button" data-id="${doc.id}">Delete</button>
      `;

      section.querySelector('.delete-button').addEventListener('click', () => {
        confirmAndDeleteDocument(doc.id);
      });

      documentsContainer.appendChild(section);
    });
  } catch (error) {
    console.error(error);
    documentsContainer.innerHTML = `<p class="error">${error.message}</p>`;
    if (error.message.includes('Unauthorized')) {
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 1500);
    }
  }
}

// Confirm and Delete Document
async function confirmAndDeleteDocument(documentId) {
  if (confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
    try {
      await deleteDocument(documentId);
      alert('Document deleted successfully.');
      await fetchAndRenderDocuments();
    } catch (error) {
      console.error(error);
      alert(`Error deleting document: ${error.message}`);
    }
  }
}

// Delete Document
async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}${DOCUMENTS_ENDPOINT}/${documentId}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete document.');
  }
}

// Format Bytes
function formatBytes(bytes, decimals = 2) {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// Handle Logout
async function handleLogout() {
  try {
    await logoutUser();
    window.location.href = 'login.html';
  } catch (error) {
    console.error('Logout Error:', error);
    alert('An error occurred during logout. Please try again.');
  }
}

// Upload Document
async function uploadDocument(file, description) {
    const formData = new FormData();
    formData.append('description', description || '');
    formData.append('file', file);
  
    const response = await fetch(`${API_BASE_URL}${UPLOAD_ENDPOINT}`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
  
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Error uploading document: ${errorData.detail || response.statusText}`);
    }
  
    alert('Document uploaded successfully!');
}
// Event Listeners
logoutButton.addEventListener('click', handleLogout);
uploadButton.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (file) {
    const description = prompt('Enter a description for the document:', '');
    await uploadDocument(file, description);
    await fetchAndRenderDocuments();
  }
});


// Check Admin Access on Load
initializeAuthListener();