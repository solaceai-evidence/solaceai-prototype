import React from 'react';
import {
    styled,
    Box,
    Link,
    IconButton,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { Route, Routes, useLocation } from 'react-router-dom';
import { About } from './pages/About';
import { Home } from './pages/Home';
import Sidebar from './components/Sidebar';
import { CookiesProvider, useCookies } from 'react-cookie';
import { Section } from './pages/Section';
import Logo from './components/assets/logo';
import { useQueryHistory } from './components/shared';
import { COOKIES_SET_OPTIONS } from './api/utils';
import { v4 as uuidv4 } from 'uuid';

enum RoutesEnum {
    HOME = '/',
    QUERY = '/query/:taskId',
    ABOUT = '/about',
}


const DarkBackground = styled('div')`
    color: ${({ theme }) => theme.palette.text.reversed};
    background-color: ${({ theme }) => theme.palette.background.reversed};
    min-height: 100vh;
    display: flex;
    flex-direction: column;
`;
export const App = () => {
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = React.useState(false);
    const [isClosing, setIsClosing] = React.useState(false);

    const [cookiesUserId, setCookieUserId] = useCookies(['userid_v2']);
    if (!cookiesUserId.userid_v2) {
        setCookieUserId('userid_v2', { userId: uuidv4() }, COOKIES_SET_OPTIONS);
    }
    const cookieUserId: string = cookiesUserId?.userid_v2?.userId ?? 'unknown'
    console.log('App is rerendered', cookieUserId)

    const handleDrawerTransitionEnd = () => {
        setIsClosing(false);
    };
    const handleDrawerClose = () => {
        setIsClosing(true);
        setMobileOpen(false);
    };

    const handleDrawerToggle = () => {
        if (!isClosing) {
            setMobileOpen(!mobileOpen);
        }
    };

    const { history, setHistory } = useQueryHistory();

    const sidebarToggle = (
        <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' }, padding: '0', margin: '0' }}
        >
            <MenuIcon />
        </IconButton>
    )

    return (
        <CookiesProvider defaultSetOptions={{ path: '/' }}>

            <DarkBackground>
                <Box sx={{ display: 'flex', flexGrow: 1, height: '100%' }}>
                    <Sidebar
                        mobileOpen={mobileOpen}
                        handleDrawerTransitionEnd={handleDrawerTransitionEnd}
                        handleDrawerClose={handleDrawerClose}
                        drawerWidth={240}
                        history={history}
                        setHistory={setHistory}
                    />
                    <Box component="main"
                        sx={{
                            width: { xs: '100%', sm: 'calc(100% - 240px)' },
                            marginLeft: { xs: '0px', sm: '240px' },
                        }}
                    >
                        <Box sx={{ borderBottom: '1px solid rgba(250, 242, 233, 0.1)', width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: { xs: '12px 12px', sm: '16px 32px' } }}>
                            <Routes>
                                <Route key={RoutesEnum.HOME} path={RoutesEnum.HOME} element={
                                    <Box>
                                        {sidebarToggle}
                                    </Box>
                                } />
                                {[RoutesEnum.QUERY, RoutesEnum.ABOUT].map((route) => (
                                    <Route key={route} path={route} element={
                                        <Box sx={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                                            {sidebarToggle}
                                            <Link href="/" sx={{ height: '18px' }}>
                                                {Logo}
                                            </Link>
                                        </Box>
                                    } />
                                ))}
                            </Routes>
                            <Box sx={{ display: 'flex', gap: '16px' }}>
                                <Link target='_blank' underline="hover" href={`https://docs.google.com/forms/d/e/1FAIpQLSeEXy9unYmpL278qXZ8-EAL_p7PtuNY50aLNvWsXntuf3VJwQ/viewform?usp=sf_link&entry.268806865=${location.pathname}`} variant="body2" sx={{ lineHeight: '24px', color: '#26EFAC' }}>Feedback</Link>
                                <Link href={RoutesEnum.ABOUT} underline="hover" variant="body2" sx={{ lineHeight: '24px', color: '#26EFAC' }}>About</Link>
                                {/* <Link href="#">Blog Post</Link> */}
                            </Box>
                        </Box>
                        <Routes>
                            <Route key={RoutesEnum.HOME} path={RoutesEnum.HOME} element={
                                <Home history={history} setHistory={setHistory} cookieUserId={cookieUserId} />
                            } />
                            <Route key={RoutesEnum.QUERY} path={RoutesEnum.QUERY} element={
                                <Section history={history} setHistory={setHistory} cookieUserId={cookieUserId} />
                            } />
                            <Route key={RoutesEnum.ABOUT} path={RoutesEnum.ABOUT} element={<About />} />
                        </Routes>
                    </Box>
                </Box>
            </DarkBackground>
        </CookiesProvider>
    );
};