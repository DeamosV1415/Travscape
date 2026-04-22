// firebase-config.js - DO NOT MODIFY
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyAX8o3VYdzw-n0ejY0Ro3es9dyGMDG6wHU",
  authDomain: "travscape-d2792.firebaseapp.com",
  projectId: "travscape-d2792",
  storageBucket: "travscape-d2792.firebasestorage.app",
  messagingSenderId: "530648008320",
  appId: "1:530648008320:web:e887bb15ef362052338865",
  measurementId: "G-ZCP6LMRJQC"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

export { app, auth, db, googleProvider };
