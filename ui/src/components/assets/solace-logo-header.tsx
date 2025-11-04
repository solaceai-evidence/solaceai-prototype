import React from 'react';
import { Box } from '@mui/material';

const SolaceLogoHeader = (
  <Box
    component="img"
    src="/solace-logo.svg"
    alt="Solace-AI Logo"
    sx={{
      height: '32px',
      width: 'auto',
      backgroundColor: '#ef529b', // Same pink background as Home page
      borderRadius: '6px',
      padding: '4px 8px',
    }}
  />
);

export default SolaceLogoHeader;
