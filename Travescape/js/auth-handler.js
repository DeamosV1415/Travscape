// auth-handler.js
// Add this script to EVERY page that requires authentication

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { getFirestore, doc, getDoc } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';

// Firebase config - REPLACE WITH YOUR CONFIG
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

// Check authentication state
onAuthStateChanged(auth, async (user) => {
    if (user) {
        // User is logged in
        currentUser = user;

        // Fetch user data from Firestore
        try {
            const userDoc = await getDoc(doc(db, 'users', user.uid));
            if (userDoc.exists()) {
                currentUserData = userDoc.data();
                updateUIWithUserData();
            } else {
                console.warn('User document does not exist in Firestore');
                // Still update UI with basic user info from Auth
                currentUserData = {
                    fullName: user.displayName || 'User',
                    email: user.email,
                    username: user.email.split('@')[0]
                };
                updateUIWithUserData();
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
            // If Firestore is not available, use basic auth data
            if (error.code === 'unavailable' || error.code === 'not-found') {
                console.warn('Firestore not available. Using basic auth data.');
                currentUserData = {
                    fullName: user.displayName || 'User',
                    email: user.email,
                    username: user.email.split('@')[0]
                };
                updateUIWithUserData();
            }
        }

    } else {
        // User is NOT logged in - redirect to login
        const publicPages = ['login.html', 'signup.html', 'index.html'];
        const currentPage = window.location.pathname;

        // If not on a public page, redirect to login
        const isPublicPage = publicPages.some(page => currentPage.includes(page));
        if (!isPublicPage) {
            // Determine relative path to login based on current location
            if (currentPage.includes('/account/profile/')) {
                window.location.href = '../sign up/login.html';
            } else if (currentPage.includes('/main/chat/')) {
                window.location.href = '../../account/sign up/login.html';
            } else {
                window.location.href = '../account/sign up/login.html';
            }
        }
    }
});

// Update UI with user data
function updateUIWithUserData() {
    // Update profile picture in navbar
    const profileImg = document.querySelector('#profile img');
    if (profileImg && currentUser.photoURL) {
        profileImg.src = currentUser.photoURL;
    }

    // Update profile link to go to profile page
    const profileLink = document.querySelector('#profile a');
    if (profileLink) {
        // Determine relative path based on current location
        const currentPage = window.location.pathname;
        if (currentPage.includes('/home/')) {
            profileLink.href = '../account/profile/index.html';
        } else if (currentPage.includes('/main/chat/')) {
            profileLink.href = '../../account/profile/index.html';
        } else {
            profileLink.href = './index.html';
        }
    }

    // Update home page user greeting - WAIT FOR DOM
    setTimeout(() => {
        const userGreeting = document.getElementById('log-btn');
        console.log('User greeting element:', userGreeting); // Debug
        console.log('Current user data:', currentUserData); // Debug

        if (userGreeting && currentUserData) {
            const firstName = currentUserData.fullName ? currentUserData.fullName.split(' ')[0] : currentUser.displayName?.split(' ')[0] || 'User';
            userGreeting.textContent = `Welcome, ${firstName}`;
            userGreeting.style.cursor = 'pointer';

            // Make it clickable to go to profile
            userGreeting.onclick = () => {
                const currentPage = window.location.pathname;
                if (currentPage.includes('/home/')) {
                    window.location.href = '../account/profile/index.html';
                } else if (currentPage.includes('/main/chat/')) {
                    window.location.href = '../../account/profile/index.html';
                }
            };
        } else if (userGreeting) {
            // User not logged in - make it go to login page
            userGreeting.textContent = 'Log in';
            userGreeting.style.cursor = 'pointer';
            userGreeting.onclick = () => {
                const currentPage = window.location.pathname;
                if (currentPage.includes('/home/')) {
                    window.location.href = '../account/sign up/login.html';
                }
            };
        }
    }, 100); // Small delay to ensure DOM is ready

    // If on profile page, populate data
    if (window.location.pathname.includes('profile/index.html')) {
        populateProfilePage();
    }
}

// Populate profile page with user data
function populateProfilePage() {
    if (!currentUserData || !currentUser) return;

    // Update profile name
    const profileName = document.querySelector('#profile-name');
    if (profileName) {
        profileName.textContent = currentUserData.fullName || currentUser.displayName;
    }

    // Update username
    const profileUsername = document.querySelector('.profile-username');
    if (profileUsername) {
        const joinDate = new Date(currentUserData.createdAt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        profileUsername.textContent = `@${currentUser.email.split('@')[0]} • Joined ${joinDate}`;
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
    updateInfoField('Birthday', currentUserData.birthday || 'Not set');
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

// Logout function
function logout() {
    signOut(auth).then(() => {
        // Determine relative path to login based on current location
        const currentPage = window.location.pathname;
        if (currentPage.includes('/account/profile/')) {
            window.location.href = '../sign up/login.html';
        } else if (currentPage.includes('/main/chat/')) {
            window.location.href = '../../account/sign up/login.html';
        } else {
            window.location.href = '../account/sign up/login.html';
        }
    }).catch((error) => {
        console.error('Logout error:', error);
    });
}

// Make functions globally accessible
window.currentUser = () => currentUser;
window.currentUserData = () => currentUserData;
window.logout = logout;

// Example: Add logout button handler
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Handle "Plan Your Escapes" button
    const planBtn = document.getElementById('plan');
    if (planBtn) {
        planBtn.addEventListener('click', (e) => {
            if (!currentUser) {
                e.preventDefault();
                // Determine relative path to login based on current location
                const currentPage = window.location.pathname;
                if (currentPage.includes('/home/')) {
                    window.location.href = '../account/sign up/login.html';
                } else {
                    window.location.href = './account/sign up/login.html';
                }
            }
        });
    }
});