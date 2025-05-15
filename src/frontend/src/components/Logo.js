import React from 'react';

function Logo({ className }) {
  return (
    <svg
      className={className}
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Video icon */}
      <rect x="5" y="8" width="20" height="15" rx="2" fill="#61dafb" stroke="#fff" strokeWidth="1"/>
      <polygon points="14,12 14,19 18,15.5" fill="#fff"/>
      
      {/* Arrow */}
      <path d="M25 15.5L30 15.5" stroke="#61dafb" strokeWidth="2" strokeLinecap="round"/>
      <path d="M28 13L30 15.5L28 18" stroke="#61dafb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      
      {/* Audio wave */}
      <path d="M32 12V19" stroke="#61dafb" strokeWidth="2" strokeLinecap="round"/>
      <path d="M34 14V17" stroke="#61dafb" strokeWidth="2" strokeLinecap="round"/>
      <path d="M36 10V21" stroke="#61dafb" strokeWidth="2" strokeLinecap="round"/>
      
      {/* MP3 text */}
      <text x="8" y="35" fill="#61dafb" fontSize="8" fontWeight="bold">MP3</text>
    </svg>
  );
}

export default Logo; 