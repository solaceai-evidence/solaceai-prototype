/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from 'react';
import { v4 as uuidV4 } from 'uuid';
import FormatQuoteIcon from '@mui/icons-material/FormatQuote';
import { Box, Divider, Link, Popover, Typography } from '@mui/material';
import styled from 'styled-components';

import { EvidenceCardContent } from './EvidenceCardContent';
import { Evidence } from './utils';
import { PaperMetadata } from '../PaperMetadata';
import { PaperDetails } from '../../@types/AsyncTaskState';

export interface EvidenceCardProps {
  evidences: Evidence[];
  corpusId: number;
  children?: React.ReactNode;
  fullTitle: string;
  id: string;
  paperDetails?: PaperDetails
  onOpenOrClose?: (isOpen: boolean) => void;
}

// This component can either look up evidence if an id is provided
// or use existing evidence provided to it

export const EvidenceCard = (props: EvidenceCardProps): React.ReactNode => {
  const { children, paperDetails, onOpenOrClose, ...rest } = props;
  const [anchorEl, setAnchorEl] = React.useState<HTMLAnchorElement | null>(
    null,
  );

  const handleClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (event.type !== 'contextmenu') {
      event.preventDefault();
    }
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };
  const open = Boolean(anchorEl);
  const id = open ? `evidence-popover-${uuidV4()}` : undefined;

  useEffect(() => {
    if (onOpenOrClose) {
      onOpenOrClose(open);
    }
  }, [open, onOpenOrClose]);

  return (
    <Container>
      <Link
        href={`https://semanticscholar.org/p/${props.corpusId}`}
        variant="body2"
        color={'unset'}
        onClick={handleClick}
        aria-describedby={id}
      >
        {children ?? <StyledFormatQuoteIcon />}
      </Link>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
      >
        <Box sx={{ maxWidth: '600px', maxHeight: '300px', overflow: 'auto', padding: { xs: '12px 16px 8px 16px', md: '16px 24px 8px 24px' }, backgroundColor: '#08232b', color: '#FAF2E9' }}>
          {(rest?.fullTitle?.length ?? 0) > 0 ? (
            <>
              <Typography sx={{ mb: 0, mt: 0.5, fontWeight: 'bold' }} variant="h6">
                {props.corpusId > 0 ? (
                  <Link href={`https://semanticscholar.org/p/${props.corpusId}`} target='_blank' rel="noreferrer">
                    {rest.fullTitle}
                  </Link>
                ) : rest.fullTitle}
              </Typography>
              {paperDetails && (
                <Typography sx={{ mb: 1.5, mt: 0 }} variant="body2">
                  <PaperMetadata title={paperDetails.title} authors={paperDetails.authors} venue={paperDetails.venue} year={paperDetails.year} citationCount={paperDetails.n_citations ?? 0} />
                </Typography>
              )}
            </>
          ) : (
            <Typography sx={{ mb: 1.5, mt: 0.5, fontWeight: 'bold' }} variant="h6">
              {`Relevant snippets from the paper`}
            </Typography>
          )}
          {rest.evidences.length >= 0 && (
            <>
              <Divider />
              <EvidenceCardContent {...rest} />
            </>
          )}
        </Box>
      </Popover>
    </Container>
  );
};

const Container = styled.div`
  display: inline-block;
  /* margin-left: 4px; */
`;

const CardContainer = styled.div`
  padding: px;
`;

const StyledFormatQuoteIcon = styled(FormatQuoteIcon)`
  font-size: 0.7em;
  vertical-align: top;
`;
