import React, { useState, useCallback, useEffect } from 'react';
import { queryRefinement } from '../api/utils';
import './InteractiveQueryRefinement.css';

interface QueryAnalysisResult {
    analysis_summary: string;
    clarity_score: number;
    ambiguity_detection: string[];
    missing_context: string[];
    clarification_questions: string[];
    suggested_refinements: string[];
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
            setAnalysisResult(result);
        } catch (err) {
            console.error('Analysis failed:', err);
            setError('Failed to analyze query. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    }, [userId, conversationHistory]);

    const handleAnswerSubmit = useCallback(() => {
        if (!analysisResult || !currentAnswer.trim()) return;

        const question = analysisResult.clarification_questions[currentQuestionIndex];
        const newEntry: ConversationEntry = {
            question,
            answer: currentAnswer.trim()
        };

        const updatedHistory = [...conversationHistory, newEntry];
        setConversationHistory(updatedHistory);
        setCurrentAnswer('');

        // Move to next question or complete if all answered
        if (currentQuestionIndex + 1 < analysisResult.clarification_questions.length) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        } else {
            // All questions answered, proceed with refined query
            handleGenerateRefinement(updatedHistory);
        }
    }, [analysisResult, currentQuestionIndex, currentAnswer, conversationHistory]);

    const handleGenerateRefinement = useCallback(async (history: ConversationEntry[]) => {
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

    const currentQuestion = analysisResult.clarification_questions[currentQuestionIndex];
    const hasAnsweredAllQuestions = conversationHistory.length === analysisResult.clarification_questions.length;

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
            <div className="section">
                <h3 className="section-title">Query Analysis:</h3>
                <p className="analysis-text">{analysisResult.analysis_summary}</p>

                {analysisResult.clarity_score !== undefined && (
                    <div className="score-display">
                        <span className="score-label">Clarity Score:</span>
                        <span className="score-value">{analysisResult.clarity_score}/10</span>
                    </div>
                )}

                {analysisResult.ambiguity_detection.length > 0 && (
                    <div className="issue-section">
                        <h4 className="issue-title">Potential Ambiguities:</h4>
                        <ul className="issue-list">
                            {analysisResult.ambiguity_detection.map((issue, idx) => (
                                <li key={idx} className="issue-item">{issue}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {analysisResult.missing_context.length > 0 && (
                    <div className="issue-section">
                        <h4 className="issue-title">Missing Context:</h4>
                        <ul className="issue-list">
                            {analysisResult.missing_context.map((context, idx) => (
                                <li key={idx} className="issue-item">{context}</li>
                            ))}
                        </ul>
                    </div>
                )}
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
            {!hasAnsweredAllQuestions && currentQuestion ? (
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
                            disabled={!currentAnswer.trim()}
                        >
                            {currentQuestionIndex + 1 < analysisResult.clarification_questions.length
                                ? 'Next Question'
                                : 'Generate Refined Query'
                            }
                        </button>
                    </div>
                </div>
            ) : (
                <div className="section action-section">
                    <h3 className="section-title">Ready to Proceed:</h3>
                    <p className="action-text">
                        All clarification questions have been answered. We can now proceed with your refined query.
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
