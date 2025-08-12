/**
 * This is the main entry point for the UI. You should not need to make any
 * changes here unless you want to update the theme.
 *
 * @see https://github.com/allenai/varnish-mui
 */
import React from 'react';
/* getTheme: create MUI theme (colors, fonts, etc) for App. 
    getRouterOverriddenTheme:  adjust theme for router-specific needs (like styling).
    VarnishApp: main wrapper component from Varnish that applies the theme and global styles.
    Varnish: AllenAI MUI-based design system. 
*/
import { getTheme, getRouterOverriddenTheme, VarnishApp } from '@allenai/varnish2';
/* API for rendering app into the DOM (replaces ReactDOM.render) */
import { createRoot } from 'react-dom/client';
/* Provides client-side routing for the app, enabling navigation between pages without full reloads. */
import { BrowserRouter } from 'react-router-dom';
/* special link component for navigating to anchor  */
import { HashLink } from 'react-router-hash-link';

import { App } from './App';
import { ScrollToTopOnPageChange } from './components/shared';

const VarnishedApp = () => {
    const theme = getTheme(getRouterOverriddenTheme(HashLink));

    return (
        <BrowserRouter>
            <ScrollToTopOnPageChange />
            <VarnishApp theme={theme}>
                <App />
            </VarnishApp>
        </BrowserRouter>
    );
};

const container = document.getElementById('root');
if (!container) {
    throw new Error("No element with an id of 'root' was found.");
}
const root = createRoot(container);
root.render(<VarnishedApp />);
