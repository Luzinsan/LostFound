import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Destinations from './pages/Destinations';
import About from './pages/About';
import LocationsList from './pages/LocationsList';
import LocationDetails from './pages/LocationDetails';
import CityDetails from './pages/CityDetails';
import './styles/globals.css';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/destinations" element={<Destinations />} />
        <Route path="/destinations/:cityName" element={<CityDetails />} />
        <Route path="/about" element={<About />} />
        <Route path="/locations" element={<LocationsList />} />
        <Route path="/locations/:locationId" element={<LocationDetails />} />
      </Routes>
    </Router>
  );
};

export default App; 