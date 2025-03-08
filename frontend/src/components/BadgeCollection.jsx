import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IoCloseOutline, IoLockClosedOutline, IoRibbonOutline } from 'react-icons/io5';

const BadgeCollection = ({ badges, onClose }) => {
  const [selectedBadge, setSelectedBadge] = useState(null);
  
  const categories = [...new Set(badges.map(badge => badge.category))];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm p-4">
      <motion.div 
        className="relative bg-gray-800/90 border border-gray-700/70 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden shadow-2xl"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
      >
        <div className="sticky top-0 z-10 bg-gray-800/90 backdrop-blur-sm p-5 border-b border-gray-700/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-purple-600/20 p-2 rounded-full mr-3">
                <IoRibbonOutline className="text-purple-400 text-xl" />
              </div>
              <h2 className="text-2xl font-bold text-white">Achievement Badges</h2>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-full transition-colors"
            >
              <IoCloseOutline className="text-gray-400 hover:text-white text-2xl" />
            </button>
          </div>
        </div>
        
        <div className="p-5 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Badge Category Tabs */}
          <div className="flex space-x-2 mb-6 overflow-x-auto pb-2">
            {categories.map(category => (
              <button
                key={category}
                className="px-4 py-2 bg-gray-700/50 hover:bg-gray-700 text-gray-300 hover:text-white rounded-lg whitespace-nowrap transition-colors"
              >
                {category}
              </button>
            ))}
          </div>
          
          {/* Badge Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {badges.map((badge) => (
              <motion.div
                key={badge.id}
                className={`relative ${
                  badge.unlocked 
                    ? "cursor-pointer" 
                    : "opacity-60 cursor-not-allowed"
                } bg-gray-700/40 border ${
                  badge.unlocked 
                    ? "border-gray-600/50" 
                    : "border-gray-700/50"
                } rounded-xl p-4 flex flex-col items-center`}
                whileHover={badge.unlocked ? { scale: 1.05 } : {}}
                onClick={() => badge.unlocked && setSelectedBadge(badge)}
              >
                <div className={`w-16 h-16 mb-3 rounded-full flex items-center justify-center ${
                  badge.unlocked
                    ? `bg-${badge.color}-600/20 border border-${badge.color}-500/30`
                    : "bg-gray-800/70"
                }`}>
                  {badge.unlocked ? (
                    <span className="text-3xl">{badge.icon}</span>
                  ) : (
                    <IoLockClosedOutline className="text-gray-500 text-xl" />
                  )}
                </div>
                <h3 className="text-sm font-medium text-center text-white mb-1">
                  {badge.name}
                </h3>
                <p className="text-xs text-gray-400 text-center">
                  {badge.unlocked ? badge.shortDescription : "Locked"}
                </p>
                {badge.unlocked && badge.earnedDate && (
                  <span className="mt-2 text-xs text-gray-500">
                    Earned {new Date(badge.earnedDate).toLocaleDateString()}
                  </span>
                )}
                {!badge.unlocked && badge.progress && (
                  <div className="mt-2 w-full">
                    <div className="text-xs text-gray-500 flex justify-between mb-1">
                      <span>Progress</span>
                      <span>{badge.progress.current}/{badge.progress.required}</span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-1.5">
                      <div 
                        className="bg-gray-600 h-1.5 rounded-full" 
                        style={{ width: `${(badge.progress.current / badge.progress.required) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
        
        {/* Badge Detail Modal */}
        <AnimatePresence>
          {selectedBadge && (
            <motion.div 
              className="fixed inset-0 z-60 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedBadge(null)}
            >
              <motion.div 
                className="bg-gray-800 border border-gray-700 rounded-xl p-6 max-w-md w-full mx-4"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={e => e.stopPropagation()}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center bg-${selectedBadge.color}-600/20 border border-${selectedBadge.color}-500/30 mr-3`}>
                      <span className="text-2xl">{selectedBadge.icon}</span>
                    </div>
                    <h3 className="text-xl font-bold text-white">{selectedBadge.name}</h3>
                  </div>
                  <button 
                    onClick={() => setSelectedBadge(null)}
                    className="p-1 hover:bg-gray-700 rounded-full"
                  >
                    <IoCloseOutline className="text-gray-400 hover:text-white text-xl" />
                  </button>
                </div>
                
                <p className="text-gray-300 mb-4">{selectedBadge.description}</p>
                
                <div className="text-sm text-gray-400 mb-2">
                  <span>Earned on {new Date(selectedBadge.earnedDate).toLocaleDateString()}</span>
                </div>
                
                <div className="bg-gray-700/50 rounded-lg p-3 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">XP Awarded</span>
                    <span className="text-blue-400 font-medium">+{selectedBadge.xpAwarded} XP</span>
                  </div>
                </div>
                
                {selectedBadge.reward && (
                  <div className="bg-purple-900/30 border border-purple-700/30 rounded-lg p-3">
                    <h4 className="text-purple-300 font-medium mb-1">Special Reward</h4>
                    <p className="text-gray-300">{selectedBadge.reward}</p>
                  </div>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default BadgeCollection;