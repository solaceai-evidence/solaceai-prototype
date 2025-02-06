import React from 'react';
import { Box } from '@mui/material';
import { useParams } from "react-router-dom";
import { Results } from '../components/Results';
import { historyType } from '../components/shared';


interface Props {
  history: historyType;
  setHistory: (history: historyType) => void;
  cookieUserId: string;
}

export const Section: React.FC<Props>  = (props)=> {
  const { history, setHistory, cookieUserId } = props;
  const { taskId } = useParams();

  return (
    <Box sx={{ padding: {xs: '16px', sm: '32px'}, width: '100%', maxWidth: '1200px' }}>
      {taskId && <Results taskId={taskId} key={taskId} history={history} setHistory={setHistory} cookieUserId={cookieUserId} />}
    </Box>
  );
};
