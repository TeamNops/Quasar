import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import IconsCarousel from './IconsCarousel';

const Dashboard = () => {
  const navigate = useNavigate();
  const [userData, setUserData] = useState({});
  const [assessmentResults, setAssessmentResults] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (!isLoggedIn) {
      navigate('/login');
      return;
    }

    // Load assessment results from localStorage
    const storedResults = localStorage.getItem('skillAssessmentResults');
    if (storedResults) {
      setAssessmentResults(JSON.parse(storedResults));
    }
    
    // In a real app, you would fetch the user's data and assessment results from the backend
    setIsLoading(false);
  }, [navigate]);

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <section className="relative min-h-screen px-4 py-12 pt-28">
      {/* Background Icon Carousel */}
      <div className="absolute inset-0 overflow-hidden">
        <IconsCarousel backgroundColor="rgba(17, 24, 39, 0.8)" iconColor="gray-500/30" />
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900/90 to-gray-800/90" />
      </div>
      
      <div className="container mx-auto relative z-10">
        <div className="bg-gray-800/60 backdrop-blur-lg border border-gray-700/50 rounded-2xl p-8 shadow-xl">
          <h1 className="text-3xl font-bold text-white mb-6">Your Dashboard</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-700/50 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Your Assessment Summary</h2>
              
              {assessmentResults ? (
                <div>
                  <div className="mb-4">
                    <p className="text-gray-300">Level: <span className="text-blue-400 font-medium capitalize">{assessmentResults.assessed_level}</span></p>
                    <p className="text-gray-300">Score: <span className="text-blue-400 font-medium">{assessmentResults.score?.percentage?.toFixed(0)}%</span></p>
                  </div>
                  
                  <h3 className="font-medium text-white mb-2">Focus Areas:</h3>
                  <ul className="text-gray-300 space-y-1 mb-4">
                    {assessmentResults.skill_gaps?.areas?.map((area, index) => (
                      <li key={index} className="flex items-center">
                        <span className={`h-2 w-2 rounded-full mr-2 ${area.level === 'needs improvement' ? 'bg-amber-400' : 'bg-green-400'}`}></span>
                        {area.skill}
                      </li>
                    ))}
                  </ul>
                  
                  <button 
                    onClick={() => navigate('/recommendations')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    View Learning Resources
                  </button>
                </div>
              ) : (
                <div className="text-center py-6">
                  <p className="text-gray-400 mb-4">You haven't completed an assessment yet.</p>
                  <button 
                    onClick={() => navigate('/assessment')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    Take Assessment
                  </button>
                </div>
              )}
            </div>
            
            <div className="bg-gray-700/50 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
              <div className="space-y-3">
                <button 
                  onClick={() => navigate('/recommendations')}
                  className="w-full text-left px-4 py-3 bg-gray-600/50 hover:bg-gray-600 rounded-lg transition-colors text-white"
                >
                  View Learning Resources
                </button>
                <button 
                  onClick={() => {}} 
                  className="w-full text-left px-4 py-3 bg-gray-600/50 hover:bg-gray-600 rounded-lg transition-colors text-white"
                >
                  Track Your Progress
                </button>
                <button 
                  onClick={() => {}} 
                  className="w-full text-left px-4 py-3 bg-gray-600/50 hover:bg-gray-600 rounded-lg transition-colors text-white"
                >
                  Join Learning Community
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Dashboard;