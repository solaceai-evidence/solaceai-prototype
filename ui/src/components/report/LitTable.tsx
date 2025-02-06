import React, { useCallback, useEffect } from 'react';
import { Box, Button, ButtonGroup, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip, Typography, useMediaQuery } from '@mui/material';
import { Columns, TableWidget } from '../../@types/TableWidget';
import CellWithEvidence from './LitTable/CellWithEvidence';
import { InlinePaperChipWidgetWithEvidence } from '../widgets/InlinePaperChipWidgetWithEvidence';
import { SIZE } from '../widgets/InlineChipWidget';
import { CitationSrc } from '../../@types/AsyncTaskState';
import ViewListOutlinedIcon from '@mui/icons-material/ViewListOutlined';

interface Props {
  table: TableWidget;
  corpusId2Citation?: { [corpusId: string]: CitationSrc};
}

export const LitTable: React.FC<Props> = (props) => {
  const { table, corpusId2Citation } = props;
  const { columns = [], rows, cells } = table;
  const [chunkIndex, setChunkIndex] = React.useState(0);

  const matche2cols = useMediaQuery('(max-width:1100px)');
  const matche1col = useMediaQuery('(max-width:900px)');
  let COLUMN_CHUNKS_SIZE = 3;
  if (matche1col) {
    COLUMN_CHUNKS_SIZE = 1;
  } else if (matche2cols) {
    COLUMN_CHUNKS_SIZE = 2;
  }

  const columnChunks: Columns[] = [];
  for (let i = 0; i < columns.length; i += COLUMN_CHUNKS_SIZE) {
      const chunk = columns.slice(i, i + COLUMN_CHUNKS_SIZE);
      columnChunks.push(chunk);
  }

  useEffect(() => { setChunkIndex(0) }, [columnChunks.length]);

  const handleReset= useCallback(() => {
    setChunkIndex(0);
  }, []);

  const handleNext = useCallback(() => {
    setChunkIndex(old => (old + 1) % columnChunks.length);
  }, [columnChunks.length]);

  const handlePrev = useCallback(() => {
    setChunkIndex(old => (old - 1 + columnChunks.length) % columnChunks.length);
  }, [columnChunks.length]);

  if (columnChunks.length === 0 || !rows || rows?.length === 0 || !cells) {
    return null;
  }
  const selectedColumns = columnChunks[chunkIndex] ?? [];
  return (
      <TableContainer sx={{ padding: 0 }}>
        <Box sx={{ alignItems: 'center', display:'flex', justifyContent: 'space-between', marginBottom:'16px' }}>
        <Typography variant="h6" component="h6" color="Secondary" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}><ViewListOutlinedIcon fontSize='small' sx={{ marginRight: '4px' }} />Literature Comparison Table</Typography>
          {columnChunks.length > 1 && (
            <Box sx={{ alignItems: 'center', display:'flex', gap:'8px' }}>
              <Typography variant="body2">Columns:</Typography>
              <ButtonGroup variant="text" size='small' aria-label="Basic button group" sx={{ border: '1px solid rgba(240, 82, 156, 0.5)' }}>
                <Button onClick={handlePrev}>{`<`}</Button>
                <Button onClick={handleReset}>{`${chunkIndex + 1} / ${columnChunks.length}`}</Button>
                <Button onClick={handleNext}>{`>`}</Button>
              </ButtonGroup>
            </Box>
          )}
        </Box>
        <Table size="small" >
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', padding: '6px' }}>Papers</TableCell>
              {selectedColumns.map((column) => (
                <TableCell sx={{ fontWeight: 'bold', padding:'6px' }} key={column.id}>
                  <Tooltip
                    title={column.description ?? ''}
                    placement='top' arrow
                    enterDelay={200} leaveDelay={50}
                  >
                    <div>
                      {column.name}
                    </div>
                  </Tooltip>
                  </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => {
              const detail = row.paper_corpus_id ? corpusId2Citation?.[row.paper_corpus_id]?.paper : undefined;
              let paperTitle: React.ReactNode = row.display_value;
              if (detail && row.paper_corpus_id) {
                let paperTitleStr = detail.title ?? row.display_value;
                if (detail.authors.length > 0) {
                  paperTitleStr = detail.authors[0].name.split(' ').pop() as string;
                  if (detail.authors.length > 1) {
                    paperTitleStr += ' et al';
                  }
                  const cleanVenue = (detail.venue ?? '').replaceAll('&amp;', '&').replace('&nbsp;', ' ')
                  paperTitleStr += `, ${detail.year}. ${cleanVenue}.`;
                  const n_citations = detail.n_citations ?? 0;
                  if (n_citations > 0) {
                    paperTitleStr += ` (${n_citations} citation${n_citations > 1 ? 's' : ''})`;
                  }
                }
                paperTitle = (<InlinePaperChipWidgetWithEvidence 
                  evidences={[]}
                  size={SIZE.small}
                  paperDetails={detail}
                  paperTitle={paperTitleStr}
                  id={row.paper_corpus_id.toString()}
                  corpusId={row.paper_corpus_id}
                  fullTitle={row.display_value ?? detail.title ?? 'Error: Paper title unknown'}
                  noBadge
                />)
              }
              return (
                <TableRow
                  key={row.id}
                  sx={{
                    verticalAlign: 'top'
                  }}
                >
                  <TableCell sx={{ width: '160px', borderRight: '1px solid rgba(230, 230, 230, 1)', borderLeft: '1px solid rgba(230, 230, 230, 1)', padding:'6px' }}>{paperTitle}</TableCell>
                  {selectedColumns.map((column) => {
                    const key = `${row.id}_${column.id}`;
                    const cell = cells[key];
                    return (
                      <CellWithEvidence cell={cell} key={column.id}/>
                    )
                  })}
                </TableRow>
              )
            })}

          </TableBody>

        </Table>
      </TableContainer>
  );
};
