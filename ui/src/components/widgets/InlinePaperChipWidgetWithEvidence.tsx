import React from 'react';

import {
  InlinePaperChipWidgetProps,
  InlinePaperChipWidget,
} from './InlinePaperChipWidget';
import { EvidenceCard } from './EvidenceCard';
import { Evidence } from './utils';
import { PaperDetails } from 'src/@types/AsyncTaskState';
import { Badge } from '@mui/material';

interface InlinePaperChipWidgetWithEvidenceProps
  extends InlinePaperChipWidgetProps {
  evidences: Evidence[];
  fullTitle: string;
  id: string
  paperDetails?: PaperDetails
  onOpenOrClose?: (isOpen: boolean) => void;
  noBadge?: boolean;
}

export const InlinePaperChipWidgetWithEvidence: React.FC<
  InlinePaperChipWidgetWithEvidenceProps
> = (props) => {
  const { evidences, id, paperTitle, paperDetails, onOpenOrClose, noBadge, ...rest } = props;
  let paperTitleStr = paperTitle
  try {
    if (!paperTitleStr || paperTitleStr.length === 0) {
      paperTitleStr = 'no data'
    }
  } catch (e) {
    console.error('parsing paper details error', e)
  }

  return (
    <>
      <EvidenceCard
        onOpenOrClose={onOpenOrClose}
        evidences={evidences}
        corpusId={props.corpusId}
        fullTitle={rest.fullTitle}
        id={id}
        paperDetails={paperDetails}
      >
        <Badge badgeContent={noBadge ? 0 : (paperDetails?.n_citations ?? 0)} color="secondary" max={99}
          sx={{ "& .MuiBadge-badge": { fontSize: 10, height: 12, padding: '0 3px', minWidth: 10, color: 'white' } }}
        >
          <InlinePaperChipWidget id={id} {...rest} paperTitle={paperTitleStr} />
        </Badge>
      </EvidenceCard>
    </>
  );
};
