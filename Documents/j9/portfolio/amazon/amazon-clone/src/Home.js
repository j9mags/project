import React from "react";
import "./Home.css";
import Product from "./Product";

function Home() {
  return (
    <div className="home">
      <div className="home__container">
        <img
          className="home__image"
          src="https://images-eu.ssl-images-amazon.com/images/G/02/digital/video/merch2016/Hero/Covid19/Generic/GWBleedingHero_ENG_COVIDUPDATE__XSite_1500x600_PV_en-GB._CB428684220_.jpg"
          alt=""
        ></img>

        <div className="home__row">
          <Product
            id="1"
            title="Mattel GKH76 BTS Mini Vinyl Figure Jin K-Pop Merch Collectable Toy"
            price={15.99}
            image="https://m.media-amazon.com/images/I/710mOkabi2L._AC_UY218_.jpg"
            rating={5}
          />
          <Product
            id="2"
            title="Bellenne BTS Decorative Cushion Bangtanboys"
            price={19.59}
            image="https://m.media-amazon.com/images/I/51mlFD8UTaL._AC_UY218_.jpg"
            rating={5}
          />
          {/* Product */}
        </div>

        <div className="home__row">
          <Product
            id="3"
            title="BTS WORLD (Original Soundtrack)"
            price={28.25}
            image="https://m.media-amazon.com/images/I/71UxWZ4dL2L._AC_UY218_.jpg"
            rating={5}
          />
          <Product
            id="4"
            title="BTS - Love Yourself 轉 Tear [Random ver.]"
            price={24.31}
            image="https://m.media-amazon.com/images/I/51BHc6qYRwL._AC_UY218_.jpg"
            rating={5}
          />
          <Product
            id="5"
            title="BTS - Map of the Soul: Persona [Random version]"
            price={28.25}
            image="https://m.media-amazon.com/images/I/51wUYZ1HYmL._AC_UY218_.jpg"
            rating={5}
          />
        </div>
        <div className="home__row"></div>
      </div>
    </div>
  );
}

export default Home;
