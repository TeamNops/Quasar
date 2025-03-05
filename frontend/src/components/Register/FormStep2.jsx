import { motion } from 'framer-motion';
import { IoPerson, IoLocationOutline } from 'react-icons/io5';
import { MdWork } from 'react-icons/md';

const FormStep2 = ({ 
  registerStep2, 
  handleSubmitStep2, 
  errorsStep2, 
  onSubmitStep2,
  setStep,
  pageVariants,
  isLoading
}) => {
  return (
    <motion.form
      key="step2"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      onSubmit={handleSubmitStep2(onSubmitStep2)}
    >
      {/* Form fields remain the same */}
      {/* ... */}
      
      {/* Updated buttons with loading state */}
      <div className="flex space-x-2 mt-4">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="w-1/3 bg-gray-700 text-white py-2 px-3 rounded-lg text-sm font-medium hover:bg-gray-600 transition-colors"
          disabled={isLoading}
        >
          Back
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="w-2/3 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-3 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creating Account...
            </>
          ) : (
            "Create Account"
          )}
        </button>
      </div>
    </motion.form>
  );
};

export default FormStep2;