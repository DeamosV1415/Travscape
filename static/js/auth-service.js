// auth-service.js
import { 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword, 
    signInWithPopup, 
    updateProfile 
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { doc, setDoc, getDoc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";
import { auth, db, googleProvider } from "./firebase-config.js";

// Sign up with email and password
export const signUpWithEmail = async (email, password, fullName, username) => {
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        // Update profile with full name
        await updateProfile(user, { displayName: fullName });

        // Create user document in Firestore (non-blocking — don't fail auth if this fails)
        try {
            await setDoc(doc(db, "users", user.uid), {
                fullName,
                username,
                email,
                createdAt: new Date().toISOString(),
                trips: [],
                countries: 0,
                followers: 0
            });
        } catch (firestoreErr) {
            console.warn("Firestore profile creation failed (auth still succeeded):", firestoreErr.message);
        }

        return { user, error: null };
    } catch (error) {
        console.error("Error signing up:", error);
        return { user: null, error: error.message };
    }
};

// Sign in with email and password
export const signInWithEmail = async (email, password) => {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { user: userCredential.user, error: null };
    } catch (error) {
        console.error("Error signing in:", error);
        return { user: null, error: error.message };
    }
};

// Sign in with Google
export const signInWithGoogle = async () => {
    try {
        const result = await signInWithPopup(auth, googleProvider);
        const user = result.user;

        // Check/create user document (non-blocking — don't fail auth if this fails)
        try {
            const userDoc = await getDoc(doc(db, "users", user.uid));
            if (!userDoc.exists()) {
                await setDoc(doc(db, "users", user.uid), {
                    fullName: user.displayName,
                    username: user.email.split('@')[0],
                    email: user.email,
                    createdAt: new Date().toISOString(),
                    trips: [],
                    countries: 0,
                    followers: 0
                });
            }
        } catch (firestoreErr) {
            console.warn("Firestore profile check failed (auth still succeeded):", firestoreErr.message);
        }

        return { user, error: null };
    } catch (error) {
        console.error("Error with Google sign-in:", error);
        return { user: null, error: error.message };
    }
};
