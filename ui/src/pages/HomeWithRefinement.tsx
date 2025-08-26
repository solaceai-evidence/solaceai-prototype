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
    { query: 'How can we tackle mental health problems and substance misuse in displaced communities in Ethiopia?', shortName: 'How can we tackle mental health problems and substance misuse in displaced communities in Ethiopia?' },
    { query: 'What is the best way to deal with cholera risks after flooding in South Africa?', shortName: 'What is the best way to deal with cholera risks after flooding in South Africa?' },
    { query: 'What is the protocol to respond to arborius outbreaks?', shortName: 'What is the protocol to respond to arborius outbreaks?' },
    { query: 'How does extreme heat hit the heart, especially for vulnerable people in India?', shortName: 'How does extreme heat hit the heart, especially for vulnerable people in India?' },
    { query: 'How is climate change raising the risk of anthrax in Somaliland?', shortName: 'How is climate change raising the risk of anthrax in Somaliland?' },
    { query: 'How is climate change affecting respiratory disease in Scotland, and what can we do about it?', shortName: 'How is climate change affecting respiratory disease in Scotland, and what can we do about it?' },
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
                            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px' }}>
                                <Box sx={{ width: '100%', maxWidth: '400px', textAlign: 'center' }}>
                                    <img src={solaceaiLogo} alt="Solace AI" style={{ width: '100%', height: 'auto' }} />
                                </Box>
                                <Typography variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center', color: '#FAF2E9' }}>
                                    Ask questions about humanitarian evidence
                                </Typography>
                                <Typography variant="body1" sx={{ textAlign: 'center', color: '#D4C7B8', maxWidth: '600px' }}>
                                    Get AI-powered insights from scientific literature to help inform your humanitarian decisions
                                </Typography>
                            </Box>

                            <MessageBar
                                onSend={handleSubmit}
                                cookieUserId={cookieUserId}
                                placeholder="Ask a question about humanitarian evidence..."
                            />

                            <Box>
                                <Typography variant="h6" sx={{ mb: 2, color: '#FAF2E9' }}>
                                    Example questions:
                                </Typography>
                                <Grid container spacing={2}>
                                    {SUGGESTIONS.map((suggestion, index) => (
                                        <Grid item xs={12} md={6} key={index}>
                                            <SuggestionCard
                                                onClick={() => handleSuggestionClick(suggestion.query)}
                                            >
                                                <Typography variant="body2" sx={{ color: '#D4C7B8' }}>
                                                    {suggestion.shortName}
                                                </Typography>
                                            </SuggestionCard>
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
            </Box>
        </>
    );
};

const SuggestionCard = styled(Box)(({ theme }) => ({
    padding: '16px',
    borderRadius: '8px',
    background: 'rgba(250, 242, 233, 0.05)',
    border: '1px solid rgba(250, 242, 233, 0.1)',
    cursor: 'pointer',
    transition: 'all 0.2s ease-in-out',
    '&:hover': {
        background: 'rgba(250, 242, 233, 0.1)',
        borderColor: 'rgba(15, 203, 140, 0.3)',
        transform: 'translateY(-2px)',
    },
}));
