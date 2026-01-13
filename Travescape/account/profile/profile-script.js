// profile-script.js - Handle profile editing functionality
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth, onAuthStateChanged, updateProfile } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { getFirestore, doc, getDoc, setDoc } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';

// Firebase config
const firebaseConfig = {
    apiKey: "AIzaSyDyTjUQM4kg4EBjrkIWBAlup_lQVAncqm4",
    authDomain: "travescape-89164.firebaseapp.com",
    projectId: "travescape-89164",
    storageBucket: "travescape-89164.firebasestorage.app",
    messagingSenderId: "823041925414",
    appId: "1:823041925414:web:30d29c27aff6b96733a1e7",
    measurementId: "G-CMXEGP7YW7"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

let currentUser = null;
let currentUserData = null;

// Wait for auth state
onAuthStateChanged(auth, async (user) => {
    if (user) {
        currentUser = user;
        await loadUserData();
    } else {
        // Redirect to login if not authenticated
        window.location.href = '../sign up/login.html';
    }
});

// Load user data from Firestore
async function loadUserData() {
    try {
        const userDoc = await getDoc(doc(db, 'users', currentUser.uid));
        if (userDoc.exists()) {
            currentUserData = userDoc.data();
            populateProfilePage();
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Populate profile page with user data
function populateProfilePage() {
    if (!currentUserData || !currentUser) return;

    // Update profile name
    const profileName = document.getElementById('profile-name');
    if (profileName) {
        profileName.textContent = currentUserData.fullName || currentUser.displayName || 'User';
    }

    // Update username
    const profileUsername = document.querySelector('.profile-username');
    if (profileUsername && currentUserData.createdAt) {
        const joinDate = new Date(currentUserData.createdAt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        const username = currentUserData.username || currentUser.email.split('@')[0];
        profileUsername.textContent = `@${username} • Joined ${joinDate}`;
    }

    // Update avatar
    const avatarImg = document.querySelector('.avatar-wrapper img');
    if (avatarImg && currentUser.photoURL) {
        avatarImg.src = currentUser.photoURL;
    }

    // Update stats
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 3) {
        statNumbers[0].textContent = currentUserData.trips?.length || 0;
        statNumbers[1].textContent = currentUserData.countries || 0;
        statNumbers[2].textContent = currentUserData.followers || 0;
    }

    // Update info fields
    updateInfoField('Email', currentUserData.email);
    updateInfoField('Location', currentUserData.location || 'Not set');
    updateInfoField('Birthday', currentUserData.birthday ? formatDate(currentUserData.birthday) : 'Not set');
    updateInfoField('Phone', currentUserData.phone || 'Not set');
}

function updateInfoField(label, value) {
    const infoItems = document.querySelectorAll('.info-item');
    infoItems.forEach(item => {
        const labelEl = item.querySelector('.info-label');
        if (labelEl && labelEl.textContent === label) {
            const valueEl = item.querySelector('.info-value');
            if (valueEl) valueEl.textContent = value;
        }
    });
}

function formatDate(dateString) {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

// Modal controls
const editModal = document.getElementById('editModal');
const editProfileBtn = document.getElementById('editProfileBtn');
const closeModal = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');
const editProfileForm = document.getElementById('editProfileForm');

// Open modal
editProfileBtn?.addEventListener('click', () => {
    if (currentUserData) {
        // Pre-fill form with current data
        document.getElementById('editFullName').value = currentUserData.fullName || '';
        document.getElementById('editEmail').value = currentUserData.email || '';
        document.getElementById('editLocation').value = currentUserData.location || '';
        document.getElementById('editPhone').value = currentUserData.phone || '';
        document.getElementById('editBirthday').value = currentUserData.birthday || '';
        document.getElementById('editBio').value = currentUserData.bio || '';

        editModal.classList.add('active');
    }
});

// Close modal
function closeEditModal() {
    editModal.classList.remove('active');
}

closeModal?.addEventListener('click', closeEditModal);
cancelBtn?.addEventListener('click', closeEditModal);

// Close modal when clicking outside
editModal?.addEventListener('click', (e) => {
    if (e.target === editModal) {
        closeEditModal();
    }
});

// Handle form submission
editProfileForm?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const saveBtn = editProfileForm.querySelector('.save-btn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="ri-loader-4-line"></i> Saving...';
    saveBtn.disabled = true;

    try {
        const updatedData = {
            fullName: document.getElementById('editFullName').value.trim(),
            location: document.getElementById('editLocation').value.trim(),
            phone: document.getElementById('editPhone').value.trim(),
            birthday: document.getElementById('editBirthday').value,
            bio: document.getElementById('editBio').value.trim(),
            lastUpdated: new Date().toISOString()
        };

        // Update Firestore
        await setDoc(doc(db, 'users', currentUser.uid), updatedData, { merge: true });

        // Update Firebase Auth display name if changed
        if (updatedData.fullName !== currentUser.displayName) {
            await updateProfile(currentUser, {
                displayName: updatedData.fullName
            });
        }

        // Reload user data and update UI
        await loadUserData();

        // Show success message
        showNotification('Profile updated successfully!', 'success');

        // Close modal
        closeEditModal();

    } catch (error) {
        console.error('Error updating profile:', error);
        showNotification('Failed to update profile. Please try again.', 'error');
    } finally {
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }
});

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="ri-${type === 'success' ? 'check' : 'error-warning'}-line"></i>
        ${message}
    `;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'linear-gradient(135deg, #4cd964, #3B9797)' : 'linear-gradient(135deg, #ff6b6b, #F72C5B)'};
        color: white;
        padding: 15px 25px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1rem;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
