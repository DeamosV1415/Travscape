// login-firebase.js
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth, signInWithEmailAndPassword, GoogleAuthProvider, signInWithPopup, sendPasswordResetEmail } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { getFirestore, doc, getDoc, setDoc } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';

// Firebase config - REPLACE WITH YOUR CONFIG FROM FIREBASE CONSOLE
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

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginform');
    const emailInput = document.getElementById('input');
    const passwordInput = document.getElementById('password-input');
    const submitBtn = document.getElementById('lgbtn');
    const googleBtn = document.getElementById('gl');
    const togglePassword = document.getElementById('togglePassword');
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');

    // Password Toggle
    if (togglePassword) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            togglePassword.className = type === 'password' ? 'ri-eye-line password-toggle' : 'ri-eye-off-line password-toggle';
        });
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.querySelector('.error-message');
        const successDiv = document.querySelector('.success-message');
        
        if (successDiv) successDiv.style.display = 'none';
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    }

    // Show success message
    function showSuccess(message) {
        const successDiv = document.querySelector('.success-message');
        const errorDiv = document.querySelector('.error-message');
        
        if (errorDiv) errorDiv.style.display = 'none';
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
        }
    }

    // Email/Password Login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = emailInput.value.trim();
            const password = passwordInput.value;
            
            if (!email || !password) {
                showError('Please enter both email and password!');
                return;
            }
            
            // Disable button and show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Logging in...';
            
            try {
                const userCredential = await signInWithEmailAndPassword(auth, email, password);
                const user = userCredential.user;
                
                // Update last login
                await setDoc(doc(db, 'users', user.uid), {
                    lastLogin: new Date().toISOString()
                }, { merge: true });
                
                showSuccess('Login successful! Redirecting...');
                
                // Redirect to chat page
                setTimeout(() => {
                    window.location.href = '/Travescape/main/chat/index.html';
                }, 1500);
                
            } catch (error) {
                console.error('Login error:', error);
                let errorMsg = 'Invalid email or password!';
                
                if (error.code === 'auth/user-not-found') {
                    errorMsg = 'No account found with this email!';
                } else if (error.code === 'auth/wrong-password') {
                    errorMsg = 'Incorrect password!';
                } else if (error.code === 'auth/invalid-email') {
                    errorMsg = 'Invalid email format!';
                } else if (error.code === 'auth/too-many-requests') {
                    errorMsg = 'Too many failed attempts. Try again later.';
                } else if (error.code === 'auth/invalid-credential') {
                    errorMsg = 'Invalid email or password!';
                }
                
                showError(errorMsg);
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Log in';
            }
        });
    }

    // Google Sign In
    if (googleBtn) {
        googleBtn.addEventListener('click', async () => {
            const provider = new GoogleAuthProvider();
            
            // Disable button
            googleBtn.disabled = true;
            const originalHTML = googleBtn.innerHTML;
            googleBtn.innerHTML = '<span class="loading"></span> Signing in...';
            
            try {
                const result = await signInWithPopup(auth, provider);
                const user = result.user;
                const userId = user.uid;

                // Check if user document exists
                const userDoc = await getDoc(doc(db, 'users', userId));
                
                if (!userDoc.exists()) {
                    // Generate username from email
                    let username = user.email.split('@')[0].toLowerCase();
                    username = username.replace(/[^a-z0-9_]/g, '');
                    
                    // Check if username exists, if so add numbers
                    let usernameExists = true;
                    let counter = 1;
                    let finalUsername = username;
                    
                    while (usernameExists) {
                        const usernameDoc = await getDoc(doc(db, 'usernames', finalUsername));
                        if (!usernameDoc.exists()) {
                            usernameExists = false;
                        } else {
                            finalUsername = `${username}${counter}`;
                            counter++;
                        }
                    }
                    
                    // Save username mapping
                    await setDoc(doc(db, 'usernames', finalUsername), {
                        username: finalUsername,
                        userId: userId,
                        createdAt: new Date().toISOString()
                    });

                    // Create user document
                    await setDoc(doc(db, 'users', userId), {
                        userId: userId,
                        username: finalUsername,
                        fullName: user.displayName,
                        email: user.email,
                        photoURL: user.photoURL || '',
                        location: '',
                        phone: '',
                        birthday: '',
                        bio: '',
                        trips: [],
                        countries: 0,
                        followers: 0,
                        following: 0,
                        createdAt: new Date().toISOString(),
                        lastLogin: new Date().toISOString()
                    });
                } else {
                    // Update last login
                    await setDoc(doc(db, 'users', userId), {
                        lastLogin: new Date().toISOString()
                    }, { merge: true });
                }

                showSuccess('Signed in successfully! Redirecting...');
                
                // Redirect to chat page
                setTimeout(() => {
                    window.location.href = '/Travescape/main/chat/index.html';
                }, 1500);

            } catch (error) {
                console.error('Google sign in error:', error);
                
                let errorMsg = 'Failed to sign in with Google. Please try again.';
                if (error.code === 'auth/popup-closed-by-user') {
                    errorMsg = 'Sign in cancelled. Please try again.';
                } else if (error.code === 'auth/popup-blocked') {
                    errorMsg = 'Pop-up blocked by browser. Please allow pop-ups.';
                }
                
                showError(errorMsg);
                googleBtn.disabled = false;
                googleBtn.innerHTML = originalHTML;
            }
        });
    }

    // Forgot Password
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const email = emailInput.value.trim();
            
            if (!email) {
                showError('Please enter your email address first!');
                emailInput.focus();
                return;
            }
            
            try {
                await sendPasswordResetEmail(auth, email);
                showSuccess('Password reset email sent! Check your inbox.');
            } catch (error) {
                console.error('Password reset error:', error);
                
                let errorMsg = 'Failed to send password reset email.';
                if (error.code === 'auth/user-not-found') {
                    errorMsg = 'No account found with this email!';
                } else if (error.code === 'auth/invalid-email') {
                    errorMsg = 'Invalid email address!';
                }
                
                showError(errorMsg);
            }
        });
    }
});