import React from 'react';
import { Divider, Typography } from '@mui/material';
import styled from 'styled-components';

import { EvidenceCardProps } from './EvidenceCard';
import { Evidence } from './utils';

const NO_ABSTRACT = 'Click on the paper title to read the abstract on Semantic Scholar.'

export const EvidenceCardContent = (
  props: EvidenceCardProps,
): React.ReactNode => {
  const { evidences, fullTitle } = props;

  if (!evidences) {
    return null;
  }

  if (evidences.length === 0) {
    return (
        <EvidenceContainer>
          <Typography sx={{ mt: 1.5, mb: 1.5 }} variant="body2">
            {NO_ABSTRACT}
          </Typography>
        </EvidenceContainer>
        )
  }

  return (
    <>
      {evidences.map((evidence, index) => (
        <EvidenceContainer key={index}>
          <Typography sx={{ mt: 1.5, mb: 1.5 }} variant="body2">
            {evidence.text.length > 0 ?
                (fullTitle.startsWith("Model: ") ? evidence.text : `"${evidence.text}"`)
                : NO_ABSTRACT}
          </Typography>
        </EvidenceContainer>
      ))}
    </>
  );
};

const EvidenceContainer = styled.div`
  margin-top: 8px;
`;
