import React, { useEffect } from 'react';
import { Card, CardContent, CardMedia, CircularProgress, Typography } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';


import { TimeEstimate } from './TimeEstimate';
import { ErrorBoundary } from 'react-error-boundary';
import { TaskStep } from 'src/@types/AsyncTaskState';


export interface StepProgressPropType {
  steps: TaskStep[];
  estimatedTime: string;
  error?: string;
}

export const StepProgress: React.FC<StepProgressPropType> = (props) => {
  
  const { steps, estimatedTime, error } = props;
  const initStep = steps.at(0);
  const runningStep = steps.slice(1).at(-1);
  const pastSteps = steps.slice(1).slice(0, -1);


  return (
    <Card sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background:'transparent', border: '1px solid rgba(250, 242, 233, 0.6)', color:'#FAF2E9', borderRadius:'8px' }}>
      <CardContent>
        {initStep && (
          <>
            <Typography variant="h5" component="div">
              💭&nbsp;&nbsp;Researching to generate an answer...&nbsp;&nbsp;
              <ErrorBoundary fallback={<span>...</span>}>
                <TimeEstimate estimatedTime={estimatedTime} startTime={initStep.start_timestamp} />
              </ErrorBoundary>
            </Typography>
          </>
        )}
        {pastSteps.map((past) => (
          <Typography key={past.start_timestamp} variant="h6" component="pre" sx={{ opacity: 0.5 }} mb={0.8} pl={3}>
            ✅&nbsp;&nbsp;{past.description}
          </Typography>
        ))}
        {runningStep && (
          <>
            <Typography variant="h6" component="pre" pl={3}>
              ⏳&nbsp;&nbsp;{runningStep.description}
              <Typography variant="h6" component="div" pl={3}>
                <ErrorBoundary fallback={<span>...</span>}>
                  <TimeEstimate estimatedTime={runningStep.estimated_timestamp} startTime={runningStep.start_timestamp} />
                </ErrorBoundary>
              </Typography>
            </Typography>
          </>
        )}
        {error && (
            <Typography variant="h6" component="div">
              ❗&nbsp;&nbsp;{error}
            </Typography>
        )}
      </CardContent>
      <CardMedia
        component='div'
        sx={{ width: 60, minWidth: 60 }}
      >
        {!error ? (
          <CircularProgress />
        ) : (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <ErrorOutlineIcon color='error' fontSize='large' />
            </div>
        )}
      </CardMedia>
    </Card>
  );
};
