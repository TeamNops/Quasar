import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { IoLockClosed } from 'react-icons/io5';
import IconsCarousel from '../IconsCarousel';

import FormStep1 from './FormStep1';
import FormStep2 from './FormStep2';
import SuccessStep from './SuccessStep';
import ProgressSteps from './ProgressSteps';

const Register = () => {
  const [step, setStep] = useState(1);
  
  // React Hook Form setup for step 1
  const { 
    register: registerStep1, 
    handleSubmit: handleSubmitStep1, 
    watch: watchStep1,
    formState: { errors: errorsStep1 }
  } = useForm({
    mode: 'onBlur',
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: ''
    }
  });
  
  // React Hook Form setup for step 2
  const { 
    register: registerStep2, 
    handleSubmit: handleSubmitStep2,
    formState: { errors: errorsStep2 } 
  } = useForm({
    mode: 'onBlur',
    defaultValues: {
      firstName: '',
      lastName: '',
      location: '',
      role: ''
    }
  });
  
  // Handle step 1 submission
  const onSubmitStep1 = (data) => {
    localStorage.setItem('registerStep1', JSON.stringify(data));
    setStep(2);
  };

  // Handle step 2 submission (final form submission)
  const onSubmitStep2 = (data) => {
    const step1Data = JSON.parse(localStorage.getItem('registerStep1'));
    
    const userData = {
      // Users table data
      email: step1Data.email,
      password: step1Data.password,
      registration_date: new Date().toISOString(),
      status: 'active',
      
      // UserProfiles table data
      profile: {
        first_name: data.firstName,
        last_name: data.lastName,
        location: data.location,
        role: data.role
      }
    };
    
    console.log('Registration data:', userData);
    setStep(3);
  };

  // Animation variants
  const pageVariants = {
    initial: { opacity: 0, x: 100 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -100 }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 py-12 pt-28">
      {/* Background Icon Carousel */}
      <div className="absolute inset-0 overflow-hidden">
        <IconsCarousel backgroundColor="rgba(17, 24, 39, 0.8)" iconColor="gray-500/30" />
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900/90 to-gray-800/90" />
      </div>

      <div className="w-full max-w-sm relative z-10">
        <motion.div 
          className="bg-gray-800/60 backdrop-blur-lg border border-gray-700/50 rounded-2xl p-6 shadow-xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {/* Logo and title */}
          <div className="text-center mb-6">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
              <IoLockClosed className="text-white text-xl" />
            </div>
            <h1 className="text-2xl font-bold text-white">Create Account</h1>
            <p className="text-gray-400 mt-1 text-sm">Start your learning journey with us</p>
          </div>

          {/* Progress steps */}
          <ProgressSteps currentStep={step} />

          {/* Form steps */}
          {step === 1 && (
            <FormStep1 
              registerStep1={registerStep1}
              handleSubmitStep1={handleSubmitStep1}
              watchStep1={watchStep1}
              errorsStep1={errorsStep1}
              onSubmitStep1={onSubmitStep1}
              pageVariants={pageVariants}
            />
          )}

          {step === 2 && (
            <FormStep2
              registerStep2={registerStep2}
              handleSubmitStep2={handleSubmitStep2}
              errorsStep2={errorsStep2}
              onSubmitStep2={onSubmitStep2}
              setStep={setStep}
              pageVariants={pageVariants}
            />
          )}

          {step === 3 && (
            <SuccessStep pageVariants={pageVariants} />
          )}

          {/* Login link */}
          <div className="mt-5 text-center">
            <p className="text-gray-400 text-xs">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">
                Log in
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Register;