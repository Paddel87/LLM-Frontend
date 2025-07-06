import React from 'react';
import { Camera } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center items-center">
      <h1 className="text-4xl font-bold text-blue-600 mb-4">LLM Frontend</h1>
      <p className="text-lg text-gray-700 mb-8">Module 1: UI Development</p>
      <div className="flex items-center space-x-2">
        <Camera className="text-gray-500" />
        <p className="text-gray-600">Welcome to the UI module!</p>
      </div>
    </div>
  );
}

export default App;