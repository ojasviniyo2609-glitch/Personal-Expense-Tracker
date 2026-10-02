import { initializeApp } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js";

import { getAuth } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";

import { getFirestore } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js";


const firebaseConfig = {
    apiKey: "AIzaSyCHOsnVfWhElWXCP7iAx58I50aUS3QHr10",
    authDomain: "personal-expense-tracker-web.firebaseapp.com",
    projectId: "personal-expense-tracker-web",
    storageBucket: "personal-expense-tracker-web.firebasestorage.app",
    messagingSenderId: "528711825126",
    appId: "1:528711825126:web:75d4a9db2ffa7866fb2d27",
    measurementId: "G-Z52GB2Q1SN"
};


const app = initializeApp(firebaseConfig);

const auth = getAuth(app);

const db = getFirestore(app);


export { app, auth, db };