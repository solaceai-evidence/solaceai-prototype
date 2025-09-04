import React, { useState, useCallback, useEffect } from 'react';
import { queryRefinement } from '../api/utils';
import './InteractiveQueryRefinement.css';

interface QueryAnalysisResult {
    original_query: string;
    refined_query: string;
    needs_interaction: boolean;
    status: string;
    analysis?: {
        setting_clear: boolean;
        climate_factor_clear: boolean;
        health_outcome_clear: boolean;
        temporal_scope_clear: boolean;
        needs_clarification: boolean;
    };
    refined_elements?: {
        setting?: string;
        climate_factor?: string;
        health_outcome?: string;
        temporal_scope?: string;
    };
    clarification_question?: string;
    element_type?: string;
    is_suggestion?: boolean;
    interactive_steps?: Array<{
        element_type: string;
        prompt: string;
        is_suggestion: boolean;
    }>;
    conversation_history?: Array<{
        role: string;
        message: string;
    }>;
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
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [userResponses, setUserResponses] = useState<{ [key: string]: string[] }>({});
    const [currentAnswer, setCurrentAnswer] = useState('');
    const [error, setError] = useState<string | null>(null);

    // Auto-analyze on mount
    useEffect(() => {
        performAnalysis(initialQuery);
    }, [initialQuery]);

    const performAnalysis = useCallback(async (query: string, responses?: { [key: string]: string[] }) => {
        setIsAnalyzing(true);
        setError(null);

        try {
            const result = await queryRefinement({
                query,
                user_id: userId,
                opt_in: true,
                user_responses: responses
            });

            console.log('Analysis result:', result);
            setAnalysisResult(result);

            // If refinement is complete, proceed
            if (result.status === 'complete' || !result.needs_interaction) {
                const conversationContext = result.conversation_history
                    ? result.conversation_history.map((h: { role: string; message: string }) => `${h.role}: ${h.message}`).join('\n')
                    : undefined;
                onRefinementComplete(result.refined_query, result.original_query, conversationContext);
            }
        } catch (err) {
            console.error('Analysis failed:', err);
            setError('Failed to analyze query. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    }, [userId, onRefinementComplete]);

    const handleAnswerSubmit = useCallback(() => {
        if (!analysisResult || !currentAnswer.trim() || !analysisResult.element_type) return;

        const elementType = analysisResult.element_type;
        const updatedResponses = {
            ...userResponses,
            [elementType]: [...(userResponses[elementType] || []), currentAnswer.trim()]
        };

        setUserResponses(updatedResponses);
        setCurrentAnswer('');
        setIsRefining(true);

        // Send updated responses to API
        performAnalysis(currentQuery, updatedResponses).then(() => {
            setIsRefining(false);
        });
    }, [analysisResult, currentAnswer, userResponses, currentQuery, performAnalysis]);

    const handleSkipElement = useCallback(() => {
        if (!analysisResult || !analysisResult.element_type) return;

        const elementType = analysisResult.element_type;

        // Add a "skip" response to indicate the user chose not to specify this element
        const updatedResponses = {
            ...userResponses,
            [elementType]: [...(userResponses[elementType] || []), "[SKIP]"]
        };

        setUserResponses(updatedResponses);
        setIsRefining(true);

        // Send updated responses to API
        performAnalysis(currentQuery, updatedResponses).then(() => {
            setIsRefining(false);
        });
    }, [analysisResult, userResponses, currentQuery, performAnalysis]);

    const handleSkipAll = useCallback(() => {
        onSkipRefinement(initialQuery);
    }, [initialQuery, onSkipRefinement]);

    const handleQueryEdit = useCallback(() => {
        setIsEditing(true);
    }, []);

    const handleQuerySave = useCallback(() => {
        setIsEditing(false);
        // Reset refinement state
        setUserResponses({});
        setCurrentStepIndex(0);
        // Re-analyze with the new query
        performAnalysis(currentQuery);
    }, [currentQuery, performAnalysis]);

    const getElementDisplayName = (elementType: string): string => {
        switch (elementType) {
            case 'setting':
                return 'Population/Setting';
            case 'climate_factor':
                return 'Climate Factor';
            case 'health_outcome':
                return 'Health Outcome';
            case 'temporal_scope':
                return 'Temporal Scope';
            default:
                return elementType;
        }
    }; const getElementExamples = (elementType: string): string => {
        switch (elementType) {
            case 'setting':
                return 'Examples: Sub-Saharan Africa, urban populations, displaced communities, elderly people in rural areas';
            case 'climate_factor':
                return 'Examples: extreme heat, flooding, air pollution, drought, heatwaves exceeding 35°C';
            case 'health_outcome':
                return 'Examples: cardiovascular mortality, respiratory diseases, infectious diseases, mental health outcomes';
            case 'temporal_scope':
                return 'Examples: immediate effects (hours-days), short-term (weeks-months), medium-term (1-5 years), long-term (5+ years)';
            default:
                return '';
        }
    };

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
                            onClick={handleSkipAll}
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
            <div className="section analysis-section">
                <h3 className="section-title">Query Analysis:</h3>
                <div className="analysis-details">
                    <div className="analysis-item">
                        <strong>Population/Setting Clear:</strong>
                        <span className={`status-badge ${analysisResult.analysis?.setting_clear ? 'status-yes' : 'status-no'}`}>
                            {analysisResult.analysis?.setting_clear ? 'Yes' : 'No'}
                        </span>
                    </div>
                    <div className="analysis-item">
                        <strong>Climate Factor Clear:</strong>
                        <span className={`status-badge ${analysisResult.analysis?.climate_factor_clear ? 'status-yes' : 'status-no'}`}>
                            {analysisResult.analysis?.climate_factor_clear ? 'Yes' : 'No'}
                        </span>
                    </div>
                    <div className="analysis-item">
                        <strong>Health Outcome Clear:</strong>
                        <span className={`status-badge ${analysisResult.analysis?.health_outcome_clear ? 'status-yes' : 'status-no'}`}>
                            {analysisResult.analysis?.health_outcome_clear ? 'Yes' : 'No'}
                        </span>
                    </div>
                    <div className="analysis-item">
                        <strong>Temporal Scope Clear:</strong>
                        <span className={`status-badge ${analysisResult.analysis?.temporal_scope_clear ? 'status-yes' : 'status-no'}`}>
                            {analysisResult.analysis?.temporal_scope_clear ? 'Yes' : 'No'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Show refined elements if available */}
            {(analysisResult.refined_elements?.setting || analysisResult.refined_elements?.climate_factor || analysisResult.refined_elements?.health_outcome || analysisResult.refined_elements?.temporal_scope) && (
                <div className="section">
                    <h3 className="section-title">Identified Elements:</h3>
                    <div className="refined-elements">
                        {analysisResult.refined_elements?.setting && (
                            <div className="element-item">
                                <strong>Population/Setting:</strong> {analysisResult.refined_elements.setting}
                            </div>
                        )}
                        {analysisResult.refined_elements?.climate_factor && (
                            <div className="element-item">
                                <strong>Climate Factor:</strong> {analysisResult.refined_elements.climate_factor}
                            </div>
                        )}
                        {analysisResult.refined_elements?.health_outcome && (
                            <div className="element-item">
                                <strong>Health Outcome:</strong> {analysisResult.refined_elements.health_outcome}
                            </div>
                        )}
                        {analysisResult.refined_elements?.temporal_scope && (
                            <div className="element-item">
                                <strong>Temporal Scope:</strong> {analysisResult.refined_elements.temporal_scope}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Show user responses so far */}
            {Object.keys(userResponses).length > 0 && (
                <div className="section">
                    <h3 className="section-title">Your Responses:</h3>
                    <div className="user-responses">
                        {Object.entries(userResponses).map(([elementType, responses]) => (
                            <div key={elementType} className="response-item">
                                <strong>{getElementDisplayName(elementType)}:</strong>
                                <ul>
                                    {responses.map((response, idx) => (
                                        <li key={idx} className={response === "[SKIP]" ? "skipped-response" : ""}>
                                            {response === "[SKIP]" ? "Skipped - keeping broad" : response}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Current clarification question or completion */}
            {analysisResult.needs_interaction && analysisResult.status === 'needs_clarification' && !isRefining ? (
                <div className="section question-section">
                    <h3 className="section-title">
                        Clarification Needed: {getElementDisplayName(analysisResult.element_type || '')}
                    </h3>

                    <div className="question-text">{analysisResult.clarification_question}</div>

                    <div className="examples-text">
                        {getElementExamples(analysisResult.element_type || '')}
                    </div>

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
                            Submit Answer
                        </button>
                        <button
                            className="secondary-button"
                            onClick={handleSkipElement}
                            disabled={isRefining}
                        >
                            Skip - Keep Broad
                        </button>
                    </div>

                    <div className="skip-explanation">
                        <p>💡 You can skip any clarification to keep your query broad if you prefer.</p>
                    </div>
                </div>
            ) : isRefining ? (
                <div className="section question-section">
                    <h3 className="section-title">Processing Your Response...</h3>
                    <div className="loading-container">
                        <div className="loading-spinner">🔍</div>
                        <div className="loading-text">Analyzing your response and determining next steps...</div>
                    </div>
                </div>
            ) : (
                <div className="section action-section">
                    <h3 className="section-title">Ready to Proceed!</h3>
                    <p className="action-text">
                        {analysisResult.status === 'complete'
                            ? "Your query has been refined and is ready for research."
                            : "Your query is clear enough to proceed with research."
                        }
                    </p>
                    {analysisResult.refined_query !== analysisResult.original_query && (
                        <div className="refined-query-preview">
                            <strong>Refined Query:</strong>
                            <div className="refined-query-text">{analysisResult.refined_query}</div>
                        </div>
                    )}
                    <div className="button-container">
                        <button
                            className="primary-button"
                            onClick={() => {
                                const conversationContext = analysisResult.conversation_history
                                    ? analysisResult.conversation_history.map((h: { role: string; message: string }) => `${h.role}: ${h.message}`).join('\n')
                                    : undefined;
                                onRefinementComplete(analysisResult.refined_query, analysisResult.original_query, conversationContext);
                            }}
                        >
                            🚀 Proceed with Research
                        </button>
                    </div>
                </div>
            )}

            {/* Skip All Option */}
            <div className="skip-section">
                <p className="skip-text">
                    Don't want to refine your query? You can proceed with the original question.
                </p>
                <button
                    className="secondary-button"
                    onClick={handleSkipAll}
                >
                    Skip All Refinement & Proceed
                </button>
            </div>
        </div>
    );
};
