import React, { useCallback, useEffect } from 'react'
import { TableCell as TableCellType } from '../../../@types/TableWidget'
import { Box, TableCell } from '@mui/material';
import { Evidence, getEvidence } from '../../../api/utils';
import { InlinePaperChipWidgetWithEvidence } from '../../../components/widgets/InlinePaperChipWidgetWithEvidence';
import { SIZE } from '../../../components/widgets/InlineChipWidget';

interface PropType {
  cell: TableCellType
}

const LoadingEvidence: Evidence[] = [{ text: 'Loading...' }];
const CellWithEvidence: React.FC<PropType> = (props) => {
  const { cell } = props;
  const [evidence, setEvidence] = React.useState<Evidence[] | undefined>();
  const [corpusId, setCorpusId] = React.useState<number>(0);

  const evidenceId = cell.metadata?.evidenceId as (undefined | number);
  useEffect(() => {
    setEvidence(undefined);
    setCorpusId(0);
  }, [evidenceId])

  const handleOpenOrClose = useCallback((isOpen: boolean) => {
    if (!isOpen) {
      return;
    }
    if (!evidenceId) {
      setEvidence([{ text: 'Something went wrong.' }]);
      return;
    }
    if (evidence) {
      return;
    }
    getEvidence(evidenceId).then((evidence) => {
      setEvidence(evidence.supports);
      setCorpusId(evidence.corpusId);
    })
  }, [evidenceId])
  let evidencePopup: JSX.Element | null = null;
  if (evidenceId) {
    evidencePopup = (
        <Box display="inline" ml={0}>
          <InlinePaperChipWidgetWithEvidence
            size={SIZE.small}
            id={`${evidenceId}`}
            evidences={evidence ?? LoadingEvidence}
            fullTitle={''}
            corpusId={corpusId}
            paperTitle={'(evidence)'}
            noBadge
            onOpenOrClose={handleOpenOrClose}
          />
        </Box>
        )
  } else if (cell.display_value !== 'N/A') {
    evidencePopup = (
        <Box display="inline" ml={0}>
          <InlinePaperChipWidgetWithEvidence
            size={SIZE.small}
            id='ABSTRACT'
            evidences={[]}
            fullTitle={''}
            corpusId={corpusId}
            paperTitle={'(evidence)'}
            noBadge
            onOpenOrClose={handleOpenOrClose}
          />
        </Box>
    )
  }
  return (
    <TableCell sx={{ borderRight: '1px solid rgba(230, 230, 230, 1)', padding:'6px' }}>
      {cell.display_value}
      {evidencePopup}
    </TableCell>
  )
}

export default CellWithEvidence;
