import React, { useCallback, useState } from 'react';
import {
  Box,
  Typography,
  Link,
  styled,
  alpha,
  Grid
} from '@mui/material';
import MessageBar from '../components/widgets/MessageBar';
import { useNavigate } from "react-router-dom";

import { createTask, createTaskWithRefinement } from '../api/utils';
import { historyType } from 'src/components/shared';
import { InteractiveQueryRefinement } from '../components/InteractiveQueryRefinementClean';

import '../../public/css/Home.css';
import solaceaiLogo from '../components/assets/solace-logo.svg';

const SUGGESTIONS: { query: string, shortName: string }[] = [
  { query: 'How can we tackle mental health problems and substance misuse in displaced communities in Ethiopia?', shortName: 'Ethiopia use case' },
  { query: 'What is the best way to deal with cholera risks after flooding in South Africa?', shortName: 'South Africa use case?' },
  { query: 'What is the protocol to respond to arborius outbreaks?', shortName: 'Arborius outbreaks (global) use case' },
  { query: 'How does extreme heat hit the heart, especially for vulnerable people in India?', shortName: 'India use case' },
  { query: 'How is climate change raising the risk of anthrax in Somaliland?', shortName: 'Somaliland use case' },
  { query: 'How is climate change affecting respiratory disease in Scotland, and what can we do about it?', shortName: 'Scotland use case' },
]

interface Props {
  history: historyType;
  setHistory: (history: historyType) => void;
  cookieUserId: string;
}

export const Home: React.FC<Props> = (props) => {

  const navigate = useNavigate();
  const { history, setHistory, cookieUserId } = props;
  const [showRefinement, setShowRefinement] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');

  const handleSubmit = useCallback(async (query: string, userId: string, optin: boolean = false) => {
    console.log('Query submitted:', query);
    setCurrentQuery(query);
    setShowRefinement(true);
  }, []);

  const handleRefinementComplete = useCallback(async (
    refinedQuery: string,
    originalQuery: string,
    conversationContext?: string
  ) => {
    console.log('Refinement complete:', { refinedQuery, originalQuery, conversationContext });

    try {
      const newStatus = await createTaskWithRefinement({
        query: originalQuery,
        refined_query: refinedQuery,
        conversation_context: conversationContext,
        skip_refinement: true,
        opt_in: true,
        user_id: cookieUserId
      });

      console.log('Task created:', newStatus, newStatus.task_id);

      if (newStatus.task_id) {
        navigate(`/query/${newStatus.task_id}`, { replace: true });
        if (!history[newStatus.task_id]) {
          setHistory({
            ...(history ?? {}),
            [newStatus.task_id]: {
              query: refinedQuery, // Use refined query for display
              taskId: newStatus.task_id,
              timestamp: Date.now()
            }
          });
        }
      }
    } catch (error) {
      console.error('Failed to create task:', error);
      // Fallback to original method
      handleSkipRefinement(originalQuery);
    }
  }, [navigate, history, setHistory, cookieUserId]);

  const handleSkipRefinement = useCallback(async (originalQuery: string) => {
    console.log('Skipping refinement for:', originalQuery);

    try {
      const newStatus = await createTask(originalQuery, true, cookieUserId);
      console.log('Task created without refinement:', newStatus, newStatus.task_id);

      if (newStatus.task_id) {
        navigate(`/query/${newStatus.task_id}`, { replace: true });
        if (!history[newStatus.task_id]) {
          setHistory({
            ...(history ?? {}),
            [newStatus.task_id]: {
              query: newStatus.query,
              taskId: newStatus.task_id,
              timestamp: Date.now()
            }
          });
        }
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  }, [navigate, history, setHistory, cookieUserId]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    handleSubmit(suggestion, cookieUserId, true);
  }, [handleSubmit, cookieUserId]);

  return (
    <>
      <Box sx={{ alignItems: 'center', display: 'flex', flexGrow: '1', flexDirection: 'column', justifyContent: 'center', padding: { xs: '40px 16px 16px 16px', sm: '80px 32px 32px 32px' }, width: '100%' }}>
        <Box sx={{ maxWidth: '800px', width: '100%', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {!showRefinement ? (
            <>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <Box className="home-logo-bg">
                  <img
                    src="/solace-logo.svg"
                    alt="Solace-AI Logo"
                    className="home-logo-img"
                  />
                </Box>
                <Typography variant="body2">Solace-AI can make mistakes. Check source documents by following citations.</Typography>
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
                      <SuggestedPrompt onClick={() => handleSuggestionClick(suggestion.query)}>
                        {suggestion.shortName}
                      </SuggestedPrompt>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </>
          ) : (
            <Box>
              <Typography variant="h5" sx={{ mb: 3, color: '#FAF2E9', textAlign: 'center' }}>
                Let's refine your question for better results
              </Typography>

              <InteractiveQueryRefinement
                initialQuery={currentQuery}
                userId={cookieUserId}
                onRefinementComplete={handleRefinementComplete}
                onSkipRefinement={handleSkipRefinement}
                cookieUserId={cookieUserId}
              />

              {/* Back button */}
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Link
                  component="button"
                  onClick={() => setShowRefinement(false)}
                  sx={{ color: '#0FCB8C', textDecoration: 'underline' }}
                >
                  ← Back to ask a different question
                </Link>
              </Box>
            </Box>
          )}
        </Box>
      </Box >
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