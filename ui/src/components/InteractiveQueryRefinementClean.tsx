import React, { useState, useCallback, useEffect } from 'react';
import { queryRefinement } from '../api/utils';
import './InteractiveQueryRefinement.css';

interface QueryAnalysisResult {
    original_query: string;
    refined_query: string;
    needs_clarification: boolean;
    conversation_ready: boolean;
    analysis: {
        setting_clear: boolean;
        question_complete: boolean;
        missing_element?: string;
        clarification_suggestion?: string;
    };
    clarification_question?: string;
    status: string;
}

interface ConversationEntry {
    question: string;
    answer: string;
}

interface InteractiveQueryRefinementProps {
    initialQuery: string;
    userId: string;
    onRefinementComplete: (refinedQuery: string, originalQuery: string, conversationContext?: string) => void;
    onSkipRefinement: (originalQuery: string) => void;
    cookieUserId: string;
}

export const InteractiveQueryRefinement: React.FC<InteractiveQueryRefinementProps> = ({
    initialQuery,
    userId,
    onRefinementComplete,
    onSkipRefinement,
    cookieUserId
}) => {
    const [currentQuery, setCurrentQuery] = useState(initialQuery);
    const [analysisResult, setAnalysisResult] = useState<QueryAnalysisResult | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isRefining, setIsRefining] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [conversationHistory, setConversationHistory] = useState<ConversationEntry[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [currentAnswer, setCurrentAnswer] = useState('');
    const [error, setError] = useState<string | null>(null);

    // Auto-analyze on mount
    useEffect(() => {
        performAnalysis(initialQuery);
    }, [initialQuery]);

    const performAnalysis = useCallback(async (query: string) => {
        setIsAnalyzing(true);
        setError(null);

        try {
            const conversation_context = conversationHistory.length > 0
                ? conversationHistory.map(entry => `Q: ${entry.question}\nA: ${entry.answer}`).join('\n\n')
                : undefined;

            const result = await queryRefinement({
                query,
                user_id: userId,
                opt_in: true,
                conversation_context
            });

            console.log('Analysis result:', result);

            // The API now returns a different structure, so we use it directly
            setAnalysisResult(result);
        } catch (err) {
            console.error('Analysis failed:', err);
            setError('Failed to analyze query. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    }, [userId, conversationHistory]);

    const analyzeQuery = useCallback(async (query: string, userId: string, conversationHistory: ConversationEntry[]): Promise<QueryAnalysisResult> => {
        const conversation_context = conversationHistory.length > 0
            ? conversationHistory.map(entry => `Q: ${entry.question}\nA: ${entry.answer}`).join('\n\n')
            : undefined;

        const result = await queryRefinement({
            query,
            user_id: userId,
            opt_in: true,
            conversation_context
        });

        return result;
    }, []);

    const handleAnswerSubmit = useCallback(async () => {
        if (!analysisResult || !currentAnswer.trim() || !analysisResult.clarification_question) return;

        const question = analysisResult.clarification_question;
        const newEntry: ConversationEntry = {
            question,
            answer: currentAnswer.trim()
        };

        const updatedHistory = [...conversationHistory, newEntry];
        setConversationHistory(updatedHistory);
        setCurrentAnswer('');

        // Create refined query with conversation context
        const conversation_context = updatedHistory.map(entry =>
            `Q: ${entry.question}\nA: ${entry.answer}`
        ).join('\n\n');

        const refinedQuery = `${currentQuery}\n\nAdditional context:\n${conversation_context}`;

        // Re-analyze the refined query to see if more clarification is needed
        setIsRefining(true);
        try {
            const newAnalysis = await analyzeQuery(refinedQuery, userId, updatedHistory);
            setAnalysisResult(newAnalysis);

            // If no more clarification needed, proceed to next step
            if (!newAnalysis.needs_clarification &&
                newAnalysis.analysis.setting_clear &&
                newAnalysis.analysis.question_complete &&
                !newAnalysis.analysis.missing_element) {
                onRefinementComplete(refinedQuery, initialQuery, conversation_context);
            }
            // Otherwise, the UI will show the next clarification question
        } catch (error) {
            console.error('Error re-analyzing query:', error);
            setError('Failed to process your answer. Please try again.');
        } finally {
            setIsRefining(false);
        }
    }, [analysisResult, currentAnswer, conversationHistory, currentQuery, initialQuery, userId, analyzeQuery, onRefinementComplete]); const handleGenerateRefinement = useCallback(async (history: ConversationEntry[]) => {
        const conversation_context = history.map(entry =>
            `Q: ${entry.question}\nA: ${entry.answer}`
        ).join('\n\n');

        // For now, just proceed with the current query and conversation context
        // In a full implementation, we could call the API again to generate a refined query
        onRefinementComplete(currentQuery, initialQuery, conversation_context);
    }, [currentQuery, initialQuery, onRefinementComplete]);

    const handleSkip = useCallback(() => {
        onSkipRefinement(initialQuery);
    }, [initialQuery, onSkipRefinement]);

    const handleQueryEdit = useCallback(() => {
        setIsEditing(true);
    }, []);

    const handleQuerySave = useCallback(() => {
        setIsEditing(false);
        // Re-analyze with the new query
        performAnalysis(currentQuery);
        // Reset conversation state
        setConversationHistory([]);
        setCurrentQuestionIndex(0);
    }, [currentQuery, performAnalysis]);

    if (isAnalyzing) {
        return (
            <div className="refinement-container">
                <div className="loading-container">
                    <div className="loading-spinner">🔍</div>
                    <div className="loading-text">Analyzing your question...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="refinement-container">
                <div className="error-container">
                    <div className="error-text">{error}</div>
                    <div className="button-container">
                        <button
                            className="primary-button"
                            onClick={() => performAnalysis(currentQuery)}
                        >
                            Try Again
                        </button>
                        <button
                            className="secondary-button"
                            onClick={handleSkip}
                        >
                            Skip Analysis
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!analysisResult) {
        return null;
    }

    // Clean up the clarification question text to fix formatting issues
    const cleanupClarificationQuestion = (question: string | undefined): string | undefined => {
        if (!question) return question;

        let cleaned = question.trim();

        // Fix the duplicate "What Which" issue
        cleaned = cleaned.replace(/^What Which/, 'Which');

        // Fix incomplete ending "are you most interested in?" -> "What are you most interested in?"
        cleaned = cleaned.replace(/\s+are you most interested in\?$/, ' What are you most interested in?');

        return cleaned;
    };

    // Generate a concise suggestion from missing element when suggestion is poor/duplicate
    const generateConciseSuggestion = (missingElement: string | undefined, suggestion: string | undefined): string | undefined => {
        if (!missingElement) return suggestion;

        // Clean up suggestion for comparison
        const cleanSuggestion = suggestion?.trim().replace(/\n/g, ' ').replace(/\s+/g, ' ');
        const cleanMissingElement = missingElement.trim().replace(/\n/g, ' ').replace(/\s+/g, ' ');

        // Check if suggestion contains the missing element (indicating duplication)
        const isDuplicate = cleanSuggestion && (
            cleanSuggestion.includes(cleanMissingElement) ||
            cleanMissingElement.includes(cleanSuggestion) ||
            cleanSuggestion === cleanMissingElement
        );

        // If we have a good suggestion that's different and concise, use it
        if (cleanSuggestion &&
            !isDuplicate &&
            cleanSuggestion.length < missingElement.length * 0.6 &&
            cleanSuggestion.includes('?')) {
            return cleanSuggestion;
        }

        // Generate a concise question from the missing element
        let concise = missingElement;

        // Handle "What specific interventions..." pattern
        if (concise.includes('What specific interventions') || concise.includes('specific interventions')) {
            return "What specific interventions are you most interested in?";
        }

        // Handle "Which specific..." pattern
        if (concise.includes('Which specific')) {
            const match = concise.match(/Which specific ([^?]+)/);
            if (match) {
                return `Which specific ${match[1].split(/\s+should|\s+\(/)[0].trim()} are you most interested in?`;
            }
        }

        // Handle "Please specify..." pattern
        if (concise.includes('Please specify')) {
            const match = concise.match(/Please specify (?:the )?([^(]+)/);
            if (match) {
                return `What ${match[1].trim().replace(/\s+for.*/, '')} are you focusing on?`;
            }
        }

        // Handle "What specific..." patterns generally
        if (concise.includes('What specific')) {
            const match = concise.match(/What specific ([^?]+)/);
            if (match) {
                const subject = match[1].split(/\s+are being|\s+should|\s+\(/)[0].trim();
                return `What specific ${subject} are you most interested in?`;
            }
        }

        // Generic fallback for other patterns
        if (concise.length > 100) {
            // Take first sentence and make it a question
            const firstSentence = concise.split(/[.!?]/)[0].trim();
            if (firstSentence.length > 20) {
                return `${firstSentence}?`;
            }
        }

        return "What specific aspect would you like to focus on?";
    };

    const currentQuestion = cleanupClarificationQuestion(analysisResult.clarification_question);
    const conciseSuggestion = generateConciseSuggestion(
        analysisResult.analysis.missing_element,
        analysisResult.analysis.clarification_suggestion
    );
    const hasAnsweredAllQuestions = conversationHistory.length > 0 && !analysisResult.clarification_question; // Has conversation history but no more questions

    // Determine if refinement is actually needed based on multiple factors
    const needsRefinement =
        analysisResult.needs_clarification || // API explicitly says clarification needed
        !analysisResult.analysis.setting_clear || // Setting not clear
        !analysisResult.analysis.question_complete || // Question incomplete
        Boolean(analysisResult.analysis.missing_element); // Has missing elements

    const shouldShowClarification = needsRefinement && !hasAnsweredAllQuestions && currentQuestion;

    return (
        <div className="refinement-container">
            {/* Query Display and Editing */}
            <div className="section">
                <h3 className="section-title">Your Question:</h3>
                {isEditing ? (
                    <div>
                        <textarea
                            className="edit-textarea"
                            value={currentQuery}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCurrentQuery(e.target.value)}
                            placeholder="Enter your question..."
                        />
                        <div className="button-container">
                            <button
                                className="primary-button"
                                onClick={handleQuerySave}
                            >
                                Save & Re-analyze
                            </button>
                            <button
                                className="secondary-button"
                                onClick={() => setIsEditing(false)}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="query-display">
                        <div className="query-text">{currentQuery}</div>
                        <button
                            className="edit-button"
                            onClick={handleQueryEdit}
                        >
                            ✏️ Edit
                        </button>
                    </div>
                )}
            </div>

            {/* Analysis Results */}
            {/* Analysis Results Display */}
            <div className="section analysis-section">
                <h3 className="section-title">Query Analysis:</h3>
                <div className="analysis-details">
                    <div className="analysis-item">
                        <strong>Question Complete:</strong>
                        <span className={`status-badge ${analysisResult.analysis.question_complete ? 'status-yes' : 'status-no'}`}>
                            {analysisResult.analysis.question_complete ? 'Yes' : 'No'}
                        </span>
                    </div>
                    <div className="analysis-item">
                        <strong>Setting Clear:</strong>
                        <span className={`status-badge ${analysisResult.analysis.setting_clear ? 'status-yes' : 'status-no'}`}>
                            {analysisResult.analysis.setting_clear ? 'Yes' : 'No'}
                        </span>
                    </div>
                    <div className="analysis-item">
                        <strong>Needs Clarification:</strong>
                        <span className={`status-badge ${analysisResult.needs_clarification ? 'status-no' : 'status-yes'}`}>
                            {analysisResult.needs_clarification ? 'Yes' : 'No'}
                        </span>
                    </div>
                    {analysisResult.analysis.missing_element && (
                        <div className="analysis-item">
                            <strong>Missing Element:</strong>
                            <div className="analysis-description">{analysisResult.analysis.missing_element}</div>
                        </div>
                    )}
                    {conciseSuggestion && (
                        <div className="analysis-item">
                            <strong>Suggestion:</strong>
                            <div className="analysis-description suggestion-text">{conciseSuggestion}</div>
                        </div>
                    )}
                </div>
            </div>

            {/* Conversation History */}
            {conversationHistory.length > 0 && (
                <div className="section">
                    <h3 className="section-title">Previous Clarifications:</h3>
                    <div className="conversation-list">
                        {conversationHistory.map((entry, idx) => (
                            <div key={idx} className="conversation-item">
                                <div className="conversation-question">Q: {entry.question}</div>
                                <div className="conversation-answer">A: {entry.answer}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Current Question or Complete Actions */}
            {shouldShowClarification && !isRefining ? (
                <div className="section question-section">
                    <h3 className="section-title">Clarification Needed:</h3>
                    <div className="question-text">{currentQuestion}</div>

                    <textarea
                        className="answer-textarea"
                        value={currentAnswer}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCurrentAnswer(e.target.value)}
                        placeholder="Please provide more details..."
                    />

                    <div className="button-container">
                        <button
                            className="primary-button"
                            onClick={handleAnswerSubmit}
                            disabled={!currentAnswer.trim() || isRefining}
                        >
                            {isRefining ? 'Processing...' : 'Submit Answer'}
                        </button>
                    </div>
                </div>
            ) : isRefining ? (
                <div className="section question-section">
                    <h3 className="section-title">Processing Your Answer...</h3>
                    <div className="loading-container">
                        <div className="loading-spinner">🔍</div>
                        <div className="loading-text">Analyzing your response and determining next steps...</div>
                    </div>
                </div>
            ) : needsRefinement ? (
                <div className="section question-section">
                    <h3 className="section-title">Query Needs Improvement:</h3>
                    <div className="question-text">
                        Based on the analysis, your query could benefit from more specific details. Please consider editing your question to be more precise.
                    </div>
                    <div className="button-container">
                        <button
                            className="primary-button"
                            onClick={handleQueryEdit}
                        >
                            ✏️ Edit Query for Better Results
                        </button>
                        <button
                            className="secondary-button"
                            onClick={() => onRefinementComplete(currentQuery, initialQuery)}
                        >
                            Continue Anyway
                        </button>
                    </div>
                </div>
            ) : (
                <div className="section action-section">
                    <h3 className="section-title">Ready to Proceed:</h3>
                    <p className="action-text">
                        {hasAnsweredAllQuestions
                            ? "All clarification questions have been answered. We can now proceed with your refined query."
                            : "Your query is clear and ready for research."
                        }
                    </p>
                    <div className="button-container">
                        <button
                            className="primary-button"
                            onClick={() => handleGenerateRefinement(conversationHistory)}
                        >
                            🚀 Proceed with Refined Query
                        </button>
                    </div>
                </div>
            )}

            {/* Skip Option */}
            <div className="skip-section">
                <p className="skip-text">
                    Don't want to refine your query? You can proceed with the original question.
                </p>
                <button
                    className="secondary-button"
                    onClick={handleSkip}
                >
                    Skip Refinement & Proceed
                </button>
            </div>
        </div>
    );
};
