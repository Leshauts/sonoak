import { BrowserRouter as Router } from 'react-router-dom';
import React from 'react';
import './App.css';
import SpotifyController from './components/SpotifyController';

function App() {
  return (
    <Router>
      <div className="App">
        <SpotifyController />
      </div>
    </Router>
  );
}

export default App;