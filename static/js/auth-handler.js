// auth-handler.js - DO NOT MODIFY CORE LOGIC
import {
  onAuthStateChanged,
  signOut,
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import {
  doc,
  getDoc,
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";
import { auth, db } from "./firebase-config.js";

let currentUser = null;
let currentUserData = null;

// Check authentication state
onAuthStateChanged(auth, async (user) => {
  const currentPage = window.location.pathname;
  const isAuthPage = ["login.html", "signup.html", "login/index.html", "signup/index.html"].some((page) =>
    currentPage.includes(page)
  );

  if (user) {
    currentUser = user;

    if (isAuthPage) {
      window.location.href = "/";
      return;
    }

    try {
      const userDoc = await getDoc(doc(db, "users", user.uid));
      if (userDoc.exists()) {
        currentUserData = userDoc.data();
        updateUIWithUserData();
      } else {
        currentUserData = {
          fullName: user.displayName || "User",
          email: user.email,
          username: user.email.split("@")[0],
        };
        updateUIWithUserData();
      }
    } catch (error) {
      console.error("Error fetching user data:", error);
      currentUserData = {
        fullName: user.displayName || "User",
        email: user.email,
        username: user.email.split("@")[0],
      };
      updateUIWithUserData();
    }
  } else {
    currentUser = null;
    currentUserData = null;
    updateUIForLoggedOut();
  }
});

function updateUIWithUserData() {
  // Update auth buttons in navbar
  const authButtons = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');
  const userAvatar = document.getElementById('user-avatar');
  const userName = document.getElementById('user-name');

  if (authButtons) authButtons.style.display = 'none';
  if (userMenu) {
    userMenu.style.display = 'flex';
    if (userName && currentUserData) {
      userName.textContent = currentUserData.fullName?.split(' ')[0] || 'User';
    }
    if (userAvatar && currentUser?.photoURL) {
      userAvatar.src = currentUser.photoURL;
    }
  }

  // Update profile page if on it
  if (window.location.pathname.includes('profile')) {
    populateProfilePage();
  }
}

function updateUIForLoggedOut() {
  const authButtons = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');

  if (authButtons) authButtons.style.display = 'flex';
  if (userMenu) userMenu.style.display = 'none';
}

function populateProfilePage() {
  if (!currentUserData || !currentUser) return;

  const profileName = document.getElementById('profile-name');
  const profileUsername = document.getElementById('profile-username');
  const profileAvatar = document.getElementById('profile-avatar');
  const profileEmail = document.getElementById('profile-email');

  if (profileName) profileName.textContent = currentUserData.fullName || currentUser.displayName;
  if (profileUsername) {
    const joinDate = currentUserData.createdAt 
      ? new Date(currentUserData.createdAt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
      : 'Recently';
    profileUsername.textContent = `@${currentUserData.username || currentUser.email.split('@')[0]} • Joined ${joinDate}`;
  }
  if (profileAvatar && currentUser.photoURL) {
    profileAvatar.src = currentUser.photoURL;
  }
  if (profileEmail) profileEmail.textContent = currentUserData.email;

  // Update stats
  const statTrips = document.getElementById('stat-trips');
  const statCountries = document.getElementById('stat-countries');
  const statFollowers = document.getElementById('stat-followers');

  if (statTrips) statTrips.textContent = currentUserData.trips?.length || 0;
  if (statCountries) statCountries.textContent = currentUserData.countries || 0;
  if (statFollowers) statFollowers.textContent = currentUserData.followers || 0;
}

function logout() {
  signOut(auth)
    .then(() => {
      window.location.href = "/";
    })
    .catch((error) => {
      console.error("Logout error:", error);
    });
}

// Make functions globally accessible
window.currentUser = () => currentUser;
window.currentUserData = () => currentUserData;
window.logout = logout;

document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }
});
