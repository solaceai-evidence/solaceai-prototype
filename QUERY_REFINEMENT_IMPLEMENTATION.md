# Query Refinement Implementation

## Overview

This implementation provides an interactive query refinement system for the Solace AI ScholarQA pipeline. It follows the provided pseudocode to systematically check and refine three key elements of research questions:

1. **Setting/Population** - Geographic region or population context
2. **Climate Factor** - Climate-related factor, exposure, or intervention
3. **Health Outcome** - Health outcomes of interest

## Architecture

### Core Components

#### 1. Query Refinement Engine (`api/scholarqa/preprocess/query_refiner.py`)

**Key Classes:**

- `RefinedElements` - Container for the three key elements
- `QueryRefinementAnalysis` - Analysis of query completeness
- `InteractiveRefinementStep` - Single step in refinement process
- `QueryRefinementResult` - Complete refinement result

**Key Functions:**

- `run_query_refinement_step()` - Main pipeline entry point
- `refine_research_question_interactive()` - Interactive refinement logic
- `check_element_clarity()` - LLM-based element clarity checking
- `create_interactive_refinement_steps()` - Generate refinement workflow

#### 2. LLM Prompts (`api/scholarqa/llms/prompts.py`)

**Element Checking Prompts:**

- `PROMPT_SETTING_CLARITY_CHECK` - Check if setting is clear
- `PROMPT_CLIMATE_FACTOR_CHECK` - Check if climate factor is clear
- `PROMPT_HEALTH_OUTCOME_CHECK` - Check if health outcome is clear

**Clarification Prompts:**

- `PROMPT_SETTING_CLARIFICATION` - Ask for setting clarification
- `PROMPT_CLIMATE_FACTOR_CLARIFICATION` - Ask for climate factor
- `PROMPT_HEALTH_OUTCOME_CLARIFICATION` - Ask for health outcome

**Suggestion Prompts (for broad answers):**

- `PROMPT_SETTING_SUGGESTION` - Nudge for more specific setting
- `PROMPT_CLIMATE_FACTOR_SUGGESTION` - Nudge for more specific climate factor
- `PROMPT_HEALTH_OUTCOME_SUGGESTION` - Nudge for more specific health outcome

**Reformulation:**

- `PROMPT_QUESTION_REFORMULATION` - Final query reformulation

#### 3. API Endpoint (`api/scholarqa/app.py`)

**Endpoint:** `POST /query_refinement`

Handles both initial analysis and interactive refinement with user responses.

## Usage Flow

### 1. Initial Analysis

```python
# Send initial query for analysis
{
    "query": "How does climate change affect health?",
    "opt_in": true
}

# Response indicates what clarification is needed
{
    "status": "needs_clarification",
    "needs_interaction": true,
    "clarification_question": "Your question does not mention a specific geographic region...",
    "element_type": "setting",
    "interactive_steps": [...]
}
```

### 2. Interactive Refinement

```python
# Send user responses for refinement
{
    "query": "How does climate change affect health?",
    "opt_in": true,
    "user_responses": {
        "setting": ["urban populations", "urban populations in Africa"],
        "climate_factor": ["extreme heat"],
        "health_outcome": ["cardiovascular disease"]
    }
}

# Get refined query
{
    "status": "complete",
    "refined_query": "What are the effects of extreme heat on cardiovascular disease in urban populations in Africa?",
    "refined_elements": {
        "setting": "urban populations in Africa",
        "climate_factor": "extreme heat",
        "health_outcome": "cardiovascular disease"
    }
}
```

## Implementation Details

### Element Clarity Checking

Each element is checked using specialized LLM prompts that return:

- `SETTING_CLEAR` / `SETTING_NEEDED`
- `CLIMATE_CLEAR` / `CLIMATE_NEEDED`
- `HEALTH_CLEAR` / `HEALTH_NEEDED`

### Breadth Detection

The `looks_broad()` function uses heuristics to detect when user answers are too general:

- Short answers (≤3 words)
- Contains broad terms like "global", "climate change", "health", etc.

### Suggestion System

When users provide broad answers, the system offers a gentle nudge:

- Shows their answer back to them
- Suggests they could be more specific
- Provides examples
- Accepts their choice if they decline to refine

### Conversation History

The system maintains a conversation history as `List[Tuple[str, str]]`:

- Each tuple is `(role, message)` where role is "assistant" or "user"
- Used for final query reformulation
- Can be returned to client for UI display

## Error Handling

- **Fail-open design**: If LLM calls fail, assumes elements are clear
- **Graceful degradation**: Returns original query if refinement fails
- **Cost tracking**: All LLM completions are tracked for billing
- **Comprehensive logging**: Errors logged but don't break the pipeline

## Testing

Run tests with:

```bash
cd /Users/w1214757/Dev/solaceai-prototype
PYTHONPATH=api python api/test_query_refinement.py
```

Test the API format:

```bash
python api/demo_query_refinement_api.py
```

## Integration

### Pipeline Integration

The refinement step integrates with the existing ScholarQA pipeline:

```python
from scholarqa.preprocess.query_refiner import run_query_refinement_step

# In pipeline
refinement_result, completions = run_query_refinement_step(
    query=user_query,
    llm_model="anthropic/claude-3-5-sonnet-20241022",
    user_responses=user_responses  # Optional for interactive mode
)

# Use refined query for downstream processing
processed_query = refinement_result.refined_query
```

### UI Integration

The UI can use the `/query_refinement` endpoint to:

1. **Analyze initial queries** - Check what elements need clarification
2. **Present clarification questions** - Show prompts from `interactive_steps`
3. **Collect user responses** - Gather answers for each element type
4. **Get refined queries** - Submit responses to get final refined question
5. **Display conversation flow** - Show the refinement dialogue

### Frontend Flow Example

```typescript
// 1. Initial analysis
const analysis = await fetch("/query_refinement", {
  method: "POST",
  body: JSON.stringify({ query: userQuery }),
});

// 2. If clarification needed, show questions
if (analysis.needs_interaction) {
  // Show clarification UI
  showRefinementQuestions(analysis.interactive_steps);
}

// 3. After user responds, get refined query
const refined = await fetch("/query_refinement", {
  method: "POST",
  body: JSON.stringify({
    query: userQuery,
    user_responses: collectedResponses,
  }),
});

// 4. Use refined query for main search
searchWithQuery(refined.refined_query);
```

## Configuration

The system uses the same LLM configuration as the main pipeline:

- Model: `anthropic/claude-3-5-sonnet-20241022`
- Temperature: `0.0` for analysis, `0.1` for reformulation
- Max tokens: `1024` for refinement calls
- Inherits rate limiting and cost tracking from main pipeline

## Default Fallbacks

If elements remain unspecified after refinement:

- **Setting**: "global population"
- **Climate Factor**: "climate change in general"
- **Health Outcome**: "all health outcomes"

These defaults ensure the system can always proceed with a query, even if users choose not to specify all elements.
