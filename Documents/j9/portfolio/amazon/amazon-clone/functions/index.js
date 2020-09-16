const functions = require("firebase-functions");
const express = require("express");
const cors = require("cors");
const stripe = require("stripe")(
  "sk_test_51HQ9jTJ4gWmCz5GmEl0RKDzYAIfgARhVx2emoHOePKVcvYnMkNSMyopzLsJMWypgLejbelOrzzuZoeAzxHfxh27y00TFQkMv0Z"
);

const app = express();

app.use(cors({ origin: true }));
app.use(express.json());

app.get("/", (request, response) => response.status(200).send("Test"));
app.post("/payments/create", async (request, response) => {
  const total = request.query.total;
  console.log(total);
  const paymentIntent = await stripe.paymentIntents.create({
    amount: total,
    currency: "usd",
  });
  response.status(201).send({
    clientSecret: paymentIntent.client_secret,
  });
});

exports.api = functions.https.onRequest(app);

// http://localhost:5001/clone-13043/us-central1/api
