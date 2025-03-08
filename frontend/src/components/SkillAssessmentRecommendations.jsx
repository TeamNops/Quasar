import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import IconsCarousel from './IconsCarousel';

// Import icons
import { 
  IoPlayCircleOutline, 
  IoArrowForward, 
  IoHourglassOutline, 
  IoSchoolOutline,
  IoChevronDown,
  IoChevronUp,
  IoRocketOutline,
  IoLogoYoutube
} from 'react-icons/io5';

const SkillAssessmentRecommendations = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [playlists, setPlaylists] = useState([]);
  const [expandedSkill, setExpandedSkill] = useState(null);

  // Animation variants
  const containerVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    hover: { scale: 1.02 }
  };

  useEffect(() => {
    const fetchYouTubeRecommendations = async () => {
      try {
        // Check if assessment has been completed
        const assessmentComplete = localStorage.getItem('skillAssessmentComplete');
        
        if (assessmentComplete !== 'true') {
          navigate('/assessment');
          return;
        }
  
        // Get assessment results from localStorage or let backend fetch them
        const assessmentResults = JSON.parse(localStorage.getItem('skillAssessmentResults') || '{}');
        
        let requestBody = {};
        let hasResults = false;
        
        // If we have results in localStorage, use them
        if (assessmentResults && assessmentResults.skill_gaps) {
          requestBody = assessmentResults;
          hasResults = true;
        }
        
        // Fetch YouTube recommendations from backend
        const response = await fetch('http://localhost:8000/api/youtube/recommendations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: hasResults ? JSON.stringify(requestBody) : JSON.stringify({}) // Send empty object if no results
        });
  
        if (!response.ok) {
          throw new Error('Failed to fetch recommendations');
        }
  
        const data = await response.json();
        
        // Set playlist data to state
        setPlaylists(data);
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching YouTube recommendations:', err);
        setError(err.message);
        setIsLoading(false);
      }
    };
  
    // Run this effect only once on mount
    fetchYouTubeRecommendations();
  }, []); // <-- empty dependency array prevents re-calling

  // Toggle expanded skill
  const toggleSkill = (skillIndex) => {
    setExpandedSkill(expandedSkill === skillIndex ? null : skillIndex);
  };

  const normalizeYoutubeLink = (link) => {
    if (link.startsWith('[') && link.endsWith(']')) {
      const cleaned = link.slice(1, -1).replace(/['"]/g, "");
      return cleaned.split(',')[0].trim();
    }
    return link;
  };

  // Updated getVideoId function that normalizes the URL first
  const getVideoId = (url) => {
    const normalizedUrl = normalizeYoutubeLink(url);
    const regex = /(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    const match = normalizedUrl.match(regex);
    return match ? match[1] : null;
  };

  // Handle continue to dashboard
  const handleContinue = () => {
    navigate('/dashboard');
  };

  // Handle "Give Test" button click
  const handleGiveTest = (youtubeLink) => {
    navigate('/youtube-assesment', { state: { youtubeUrl: youtubeLink } });
  };

  // Loading state
  if (isLoading) {
    return (
      <section className="relative min-h-screen flex items-center justify-center px-4 py-12 pt-28">
        <div className="absolute inset-0 overflow-hidden">
          <IconsCarousel backgroundColor="rgba(17, 24, 39, 0.8)" iconColor="gray-500/30" />
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900/90 to-gray-800/90" />
        </div>
        <div className="w-full max-w-3xl relative z-10 bg-gray-800/60 backdrop-blur-lg border border-gray-700/50 rounded-2xl p-8 shadow-xl">
          <div className="flex flex-col items-center justify-center">
            <IoHourglassOutline className="animate-pulse text-blue-500 text-5xl mb-4" />
            <h3 className="text-xl font-medium text-white mb-2">Generating personalized learning path...</h3>
            <p className="text-gray-300 text-center">We're curating videos based on your assessment results.</p>
          </div>
        </div>
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section className="relative min-h-screen flex items-center justify-center px-4 py-12 pt-28">
        <div className="absolute inset-0 overflow-hidden">
          <IconsCarousel backgroundColor="rgba(17, 24, 39, 0.8)" iconColor="gray-500/30" />
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900/90 to-gray-800/90" />
        </div>
        <div className="w-full max-w-3xl relative z-10 bg-gray-800/60 backdrop-blur-lg border border-gray-700/50 rounded-2xl p-8 shadow-xl">
          <div className="flex flex-col items-center justify-center">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h3 className="text-xl font-medium text-white mb-2">Something went wrong</h3>
            <p className="text-gray-300 text-center mb-6">{error}</p>
            <button 
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 py-12 pt-28">
      <div className="absolute inset-0 overflow-hidden">
        <IconsCarousel backgroundColor="rgba(17, 24, 39, 0.8)" iconColor="gray-500/30" />
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900/90 to-gray-800/90" />
      </div>
      <motion.div 
        className="w-full max-w-4xl relative z-10"
        variants={containerVariants}
        initial="initial"
        animate="animate"
      >
        <div className="bg-gray-800/60 backdrop-blur-lg border border-gray-700/50 rounded-2xl p-8 shadow-xl">
          <div className="text-center mb-8">
            <IoSchoolOutline className="mx-auto text-blue-500 text-5xl mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Your Personalized Learning Path</h2>
            <p className="text-gray-300 max-w-2xl mx-auto">
              Based on your assessment, we've created custom playlists to help you learn and improve.
              Click on any skill to explore recommended videos.
            </p>
          </div>
          <div className="space-y-6 mb-8">
            {playlists.length > 0 ? (
              playlists.map((skillPlaylist, skillIndex) => (
                <motion.div 
                  key={skillIndex}
                  className="border border-gray-700 rounded-xl overflow-hidden"
                  variants={itemVariants}
                  whileHover={{ scale: 1.01 }}
                >
                  <div 
                    className="bg-gray-700/50 p-4 flex justify-between items-center cursor-pointer"
                    onClick={() => toggleSkill(skillIndex)}
                  >
                    <div className="flex items-center">
                      <IoRocketOutline className="text-blue-400 text-xl mr-3" />
                      <div>
                        <h3 className="text-lg font-medium text-white">{skillPlaylist.skill}</h3>
                        <p className="text-sm text-gray-400">{skillPlaylist.playlist.length} concepts to master</p>
                      </div>
                    </div>
                    {expandedSkill === skillIndex ? (
                      <IoChevronUp className="text-blue-400 text-xl" />
                    ) : (
                      <IoChevronDown className="text-blue-400 text-xl" />
                    )}
                  </div>
                  {expandedSkill === skillIndex && (
                    <div className="p-4 space-y-4 bg-gray-800/70">
                      {skillPlaylist.playlist.map((item, index) => {
                        const videoId = getVideoId(item.youtube_link);
                        return (
                          <motion.div 
                            key={index}
                            className="border border-gray-600/50 rounded-lg overflow-hidden"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                          >
                            <div className="p-3 bg-gray-700/30 border-b border-gray-600/50">
                              <h4 className="font-medium text-white">{item.concept}</h4>
                            </div>
                            {videoId ? (
                              <>
                                <div className="aspect-video w-full">
                                  <iframe 
                                    width="100%" 
                                    height="100%" 
                                    src={`https://www.youtube.com/embed/${videoId}`} 
                                    title={item.concept}
                                    frameBorder="0" 
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                    allowFullScreen
                                    loading="lazy"
                                  ></iframe>
                                </div>
                                <div className="flex justify-center p-2">
                                  <button
                                    onClick={() => handleGiveTest(item.youtube_link)}
                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                                  >
                                    Give Test
                                  </button>
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="p-4 text-center bg-gray-700/10">
                                  <a 
                                    href={item.youtube_link} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors"
                                  >
                                    <IoLogoYoutube className="mr-2" />
                                    Watch on YouTube
                                  </a>
                                </div>
                                <div className="flex justify-center p-2">
                                  <button
                                    onClick={() => handleGiveTest(item.youtube_link)}
                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                                  >
                                    Give Test
                                  </button>
                                </div>
                              </>
                            )}
                          </motion.div>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              ))
            ) : (
              <div className="text-center p-8 border border-dashed border-gray-600 rounded-xl">
                <p className="text-gray-400">No learning recommendations available. Please retake the assessment.</p>
              </div>
            )}
          </div>
          <div className="flex justify-center">
            <button 
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors flex items-center"
              onClick={handleContinue}
            >
              Continue to Dashboard
              <IoArrowForward className="ml-2" />
            </button>
          </div>
        </div>
      </motion.div>
    </section>
  );
};

export default SkillAssessmentRecommendations;
