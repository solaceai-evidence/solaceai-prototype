import React from 'react';
import { Box, Typography } from '@mui/material';

const SolaceLogoHeader = (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Box
            component="img"
            src="/solace-logo.svg"
            alt="Solace-AI Logo"
            sx={{ height: '18px', width: 'auto' }}
        />
        <Typography
            variant="body2"
            sx={{
                color: 'inherit',
                fontWeight: '500',
                fontSize: '14px'
            }}
        >
            Solace-ai
        </Typography>
    </Box>
);

export default SolaceLogoHeader;
