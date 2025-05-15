import React from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';

const BaseLayout = ({ children, title = 'Lost&Found' }) => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white shadow-md">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <span className="text-2xl font-bold">Lost&Found</span>
              </Link>
            </div>
            <nav>
              <ul className="flex space-x-6">
                <li><Link to="/" className="hover:text-blue-200 transition">Home</Link></li>
                <li><Link to="/destinations" className="hover:text-blue-200 transition">Destinations</Link></li>
                <li><Link to="/locations" className="hover:text-blue-200 transition">All Locations</Link></li>
                <li><Link to="/about" className="hover:text-blue-200 transition">About</Link></li>
              </ul>
            </nav>
          </div>
        </div>
      </header>

      {/* Page Title */}
      <div className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-3">
          <h1 className="text-2xl font-semibold text-gray-800">{title}</h1>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-3">Lost&Found</h3>
              <p className="text-sm text-gray-300">
                Your personal travel discovery assistant powered by advanced NLP 
                and reliable sources for tailored travel recommendations.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Quick Links</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li><Link to="/" className="hover:text-white transition">Home</Link></li>
                <li><Link to="/destinations" className="hover:text-white transition">Destinations</Link></li>
                <li><Link to="/locations" className="hover:text-white transition">All Locations</Link></li>
                <li><Link to="/about" className="hover:text-white transition">About</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Connect</h3>
              <p className="text-sm text-gray-300 mb-2">
                Find us on Telegram: @LostAndFoundBot
              </p>
              <p className="text-sm text-gray-300">
                &copy; {new Date().getFullYear()} Lost&Found. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

BaseLayout.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string
};

export default BaseLayout; 