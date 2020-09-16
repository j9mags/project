import axios from "axios";

const instance = axios.create({
  baseURL: "https://us-central1-challenge-cbffe.cloudfunctions.net/api",
});

export default instance;
