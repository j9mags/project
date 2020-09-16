import firebase from "firebase";

const firebaseConfig = {
  apiKey: "AIzaSyDaMkZ-Ov0Uz-mp0PAYMrlF6uEi2WPJQrU",
  authDomain: "challenge-cbffe.firebaseapp.com",
  databaseURL: "https://challenge-cbffe.firebaseio.com",
  projectId: "challenge-cbffe",
  storageBucket: "challenge-cbffe.appspot.com",
  messagingSenderId: "783864353775",
  appId: "1:783864353775:web:07763f5769824ac51a9c1a",
  measurementId: "G-C1CBJ04EL1",
};

const firebaseApp = firebase.initializeApp(firebaseConfig);

const db = firebaseApp.firestore();
const auth = firebase.auth();

export { db, auth };
