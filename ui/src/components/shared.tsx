/**
 * This file is meant for shared display components that you use throughout
 * your application.
 *
 * Components with a lot of logic, or those that are particularly complicated
 * should probably be put in their own file. This file is meant for the
 * re-usable, simple things used in a lot of different spots in your UI.
 */
import React, { useCallback } from 'react';
import { useEffect } from 'react';
import { styled } from '@mui/material';
import WarningOutlined from '@mui/icons-material/WarningOutlined';
import { useLocation } from 'react-router-dom';
import { useCookies } from 'react-cookie';
import { COOKIES_SET_OPTIONS } from '../api/utils';

export type historyType = { [key: string]: { query: string, taskId: string, timestamp: number } };

export const useQueryHistory = () => {
  const [cookies, setCookie] = useCookies(['history_v2']);
  const [innerHistory, setInnerHistory] = React.useState<historyType>(cookies.history_v2 ?? {});
  if (!cookies.history_v2) {
    setInnerHistory({});
    setCookie('history_v2', {}, COOKIES_SET_OPTIONS);
  }
  const setHistory = useCallback((history: historyType) => {
    setInnerHistory(history);
    setCookie('history_v2', history, COOKIES_SET_OPTIONS);
  },[setCookie, setInnerHistory]);
  return {history: innerHistory, setHistory};
}

export const Error = ({ message }: { message: string }) => (
    <ErrorGrid>
        <WarningOutlined />
        {message}
    </ErrorGrid>
);

const TwoColumnGrid = styled('div')`
    display: grid;
    grid-template-columns: auto max-content;
    grid-gap: ${({ theme }) => theme.spacing(1)};
    align-items: center;
`;

const ErrorGrid = styled(TwoColumnGrid)`
    color: ${({ theme }) => theme.palette.error.main};
`;

export const ScrollToTopOnPageChange = () => {
    const location = useLocation();
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [location]);
    return null;
};
