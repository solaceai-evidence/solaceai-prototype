import React, { useEffect } from 'react';
import { Typography } from '@mui/material';
import { ErrorBoundary } from "react-error-boundary";


export interface ProgressPropType {
  estimatedTime: number | string;
  startTime: number;
}


export const TimeEstimate: React.FC<ProgressPropType> = (props) => {
  
  const { estimatedTime, startTime } = props;
  const formatter = new Intl.RelativeTimeFormat('en-US');
  const [seconds, setSeconds] = React.useState<number>(-1);
  useEffect(() => {
    const timeoutIds: number[] = [];
    const inner = () => {
      const startDate = new Date(startTime * 1000);
      const now = new Date()
      const newSeconds = Math.round((now.getTime()-startDate.getTime()) / 1000);
      if (!Number.isNaN(newSeconds) && Number.isFinite(newSeconds)) {
        setSeconds(newSeconds);
      }
      const timeoutId = window.setTimeout(inner, 1000);
      timeoutIds.push(timeoutId);
    }
    inner();
    return () => {
      timeoutIds.forEach(clearTimeout);
    }
  }, [startTime])

  if (startTime <= 10) {
    return <Typography sx={{ color: 'text.secondary', mb: 0 }}>---</Typography>
  }

  return (
    <Typography sx={{ color: 'rgba(250, 242, 233, 0.8)', mb: 0 }} component={'span'}>
      <ErrorBoundary fallback={<span>...</span>}>
        {/* {startTime > 1 ? `started ${timeAgo.formattedDate} ago / estimated: ${estimatedTime}` : '---'} */}
        {(startTime <= 10 || Number.isNaN(startTime)) ? '---' : (
          formatter.format(-seconds, 'second')
        )}
          {typeof estimatedTime === 'number' ? 
          ` / ${Math.round(estimatedTime - startTime)} seconds`
        : ' / ' + estimatedTime}
      </ErrorBoundary>
    </Typography>
  );
};
