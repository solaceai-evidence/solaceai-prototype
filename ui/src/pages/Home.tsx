import React, { useCallback } from 'react';
import { Box, Typography, Link, styled, alpha, Grid } from '@mui/material';
import MessageBar from '../components/widgets/MessageBar';
import { useNavigate } from 'react-router-dom';

import { createTask } from '../api/utils';
import { historyType } from 'src/components/shared';

import '../../public/css/Home.css';
import solaceaiLogo from '../components/assets/solace-logo.svg';

const SUGGESTIONS: { query: string; shortName: string }[] = [
  {
    query:
      'How can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia?',
    shortName:
      'How can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia?',
  },
  {
    query: 'What is the best way to deal with cholera risks after flooding in South Africa?',
    shortName: 'What is the best way to deal with cholera risks after flooding in South Africa?',
  },
  {
    query: 'What is the protocol to respond to arbovirus outbreaks?',
    shortName: 'What is the protocol to respond to arbovirus outbreaks?',
  },
  {
    query: 'How does extreme heat hit the heart, especially for vulnerable people in India?',
    shortName: 'How does extreme heat hit the heart, especially for vulnerable people in India?',
  },
  {
    query: 'How is climate change raising the risk of anthrax in Somaliland?',
    shortName: 'How is climate change raising the risk of anthrax in Somaliland?',
  },
  {
    query:
      'How is climate change affecting respiratory disease in Scotland, and what can we do about it?',
    shortName:
      'How is climate change affecting respiratory disease in Scotland, and what can we do about it?',
  },
];

interface Props {
  history: historyType;
  setHistory: (history: historyType) => void;
  cookieUserId: string;
}

export const Home: React.FC<Props> = (props) => {
  const navigate = useNavigate();
  const { history, setHistory, cookieUserId } = props;

  const handleSubmit = useCallback(
    async (query: string, userId: string, optin: boolean = false) => {
      console.log(query);

      const newStatus = await createTask(query, optin, userId);
      console.log(newStatus, newStatus.task_id);
      if (newStatus.task_id) {
        navigate(`/query/${newStatus.task_id}`, { replace: true });
        if (!history[newStatus.task_id]) {
          setHistory({
            ...(history ?? {}),
            [newStatus.task_id]: {
              query: newStatus.query,
              taskId: newStatus.task_id,
              timestamp: Date.now(),
            },
          });
        }
      }
    },
    [history]
  );

  return (
    <>
      <Box
        sx={{
          alignItems: 'center',
          display: 'flex',
          flexGrow: '1',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: { xs: '40px 16px 16px 16px', sm: '80px 32px 32px 32px' },
          width: '100%',
        }}
      >
        <Box
          sx={{
            maxWidth: '800px',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '24px',
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Box className="home-logo-bg">
              <img src="/solace-logo.svg" alt="Solace-AI Logo" className="home-logo-img" />
            </Box>
            <Typography variant="body2">
              Solace-AI can make mistakes. Check source documents by following citations.
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <MessageBar onSend={handleSubmit} cookieUserId={cookieUserId} />
            <Grid
              container
              direction={{ xs: 'column', sm: 'row' }}
              spacing={1}
              sx={{ alignItems: 'center' }}
            >
              {SUGGESTIONS.map((suggestion) => (
                <Grid item key={suggestion.query}>
                  <SuggestedPrompt
                    onClick={() => handleSubmit(suggestion.query, cookieUserId, true)}
                  >
                    {suggestion.shortName}
                  </SuggestedPrompt>
                </Grid>
              ))}
            </Grid>
          </Box>
        </Box>
      </Box>
    </>
  );
};

const SuggestedPrompt = styled('button')`
  border: 1px solid ${({ theme }) => alpha(theme.color['off-white'].hex, 0.1)};
  border-radius: 6px;
  background: transparent;
  color: ${({ theme }) => theme.color.N1.hex};
  cursor: pointer;
  display: flex;
  font-size: ${({ theme }) => theme.font.size.md};
  gap: ${({ theme }) => theme.spacing(1)};
  line-height: ${({ theme }) => theme.spacing(3)};
  margin-bottom: ${({ theme }) => theme.spacing(0.5)};
  padding: ${({ theme }) => theme.spacing(1, 1.5)};
  text-decoration: none !important;

  :hover {
    color: ${({ theme }) => theme.color.N5.hex};
    background: ${({ theme }) => alpha(theme.color['off-white'].hex, 0.05)};
  }

  & .MuiSvgIcon-root {
    color: ${({ theme }) => theme.color['green-100'].hex};
  }
`;

/* to control size depending on screen: <Box sx={{ height: { xs: '28px', sm: '42px' }, width: { xs: '358px', sm: '538px' } }}> */
