import React, { useEffect } from 'react';

export const About = () => {
    useEffect(() => {
        window.location.href = "https://solaceai.org/"
    }, []);
    return (
        <div>redirecting...</div>
    )
};
