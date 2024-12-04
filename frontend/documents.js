// documents.js

// Configuration
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

// Import the logoutUser function from firebase.js (if applicable)
// If you're not using module imports, you may need to adjust this
import { logoutUser } from './firebase.js'; // Adjust the path if necessary

// Fetch and Render Documents with Metadata
async function fetchAndRenderDocuments() {
  try {
    // Show loading message
    documentsContainer.innerHTML = '<p>Loading documents...</p>';

    // Fetch documents from the backend
    const response = await fetch(`${API_BASE_URL}${DOCUMENTS_ENDPOINT}`, {
      method: 'GET',
      credentials: 'include', // Include cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized. Please log in.');
      }
      throw new Error(`Error fetching documents: ${response.statusText}`);
    }

    const data = await response.json();

    // Clear the container
    documentsContainer.innerHTML = '';

    if (data.length === 0) {
      documentsContainer.innerHTML = '<p>No documents found.</p>';
      return;
    }

    // Create and append document sections
    data.forEach(doc => {
      const section = document.createElement('section');
      section.classList.add('document-section');

      // Document Title (File Name)
      const docTitle = document.createElement('h3');
      docTitle.classList.add('document-title');
      docTitle.textContent = doc.file_name || 'Unnamed Document';
      section.appendChild(docTitle);

      // Document Description
      const docDescription = document.createElement('p');
      docDescription.classList.add('document-description');
      docDescription.textContent = doc.description || 'No Description';
      section.appendChild(docDescription);

      // Document Type
      const docType = document.createElement('p');
      docType.classList.add('document-type');
      docType.innerHTML = `<strong>Type:</strong> ${doc.file_type || 'Unknown'}`;
      section.appendChild(docType);

      // File Size
      const docSize = document.createElement('p');
      docSize.classList.add('document-size');
      docSize.innerHTML = `<strong>Size:</strong> ${formatBytes(doc.size)}`;
      section.appendChild(docSize);

      // Upload Timestamp
      const docUploadedAt = document.createElement('p');
      docUploadedAt.classList.add('document-uploaded-at');
      const uploadedAt = new Date(doc.uploaded_at.seconds * 1000); // Assuming Firestore timestamp
      docUploadedAt.innerHTML = `<strong>Uploaded At:</strong> ${uploadedAt.toLocaleString()}`;
      section.appendChild(docUploadedAt);

      // View Document Link
      const docLink = document.createElement('a');
      docLink.href = doc.file_url || '#';
      docLink.textContent = 'View Document';
      docLink.target = '_blank';
      docLink.rel = 'noopener noreferrer';
      docLink.classList.add('document-link');
      section.appendChild(docLink);

      documentsContainer.appendChild(section);
    });
  } catch (error) {
    console.error(error);
    documentsContainer.innerHTML = `<p class="error">${error.message}</p>`;
    if (error.message.includes('Unauthorized')) {
      // Optionally, prompt the user to log in again
      setTimeout(() => {
        window.location.href = 'login.html'; // Adjust the path if necessary
      }, 1500);
    }
  }
}

uploadButton.addEventListener('click', () => {
    fileInput.click();
  });
  
  // Event Listener for File Input Change
  fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
      // Prompt user for description
      const description = prompt('Enter a description for the document:', '');
      await uploadDocument(file, description);
      // Refresh the documents list after upload
      fetchAndRenderDocuments();
    }
  });
  
  // Function to upload the document
  async function uploadDocument(file, description) {
    try {
      // Create FormData object
      const formData = new FormData();
      formData.append('description', description || '');
      formData.append('file', file);
  
      // Send the file to the backend
      const response = await fetch(`${API_BASE_URL}${UPLOAD_ENDPOINT}`, {
        method: 'POST',
        credentials: 'include', // Include cookies
        body: formData,
      });
  
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized. Please log in.');
        }
        const errorData = await response.json();
        throw new Error(`Error uploading document: ${errorData.detail || response.statusText}`);
      }
  
      const data = await response.json();
      alert('Document uploaded successfully!');
    } catch (error) {
      console.error(error);
      alert(`Error: ${error.message}`);
      if (error.message.includes('Unauthorized')) {
        // Optionally, prompt the user to log in again
        setTimeout(() => {
          window.location.href = 'login.html'; // Adjust the path if necessary
        }, 1500);
      }
    }
  }

// Helper function to format bytes to a readable format
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024,
    dm = decimals < 0 ? 0 : decimals,
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'],
    i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Handle Logout
async function handleLogout() {
  try {
    await logoutUser(); // Use the existing logoutUser function from firebase.js
    // Redirect to login page after successful logout
    window.location.href = 'login.html'; // Adjust the path if necessary
  } catch (error) {
    console.error('Logout Error:', error);
    alert('An error occurred during logout. Please try again.');
  }
}

// Event Listener for Logout Button
logoutButton.addEventListener('click', handleLogout);

// Initial Fetch
fetchAndRenderDocuments();