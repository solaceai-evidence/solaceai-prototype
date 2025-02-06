
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ViewListOutlinedIcon from '@mui/icons-material/ViewListOutlined';

import React, { useCallback } from 'react';
import { Box, Link, styled, Typography } from '@mui/material';
import Markdown, { MarkdownToJSX } from 'markdown-to-jsx';
import { PaperMetadataString } from '../PaperMetadataString';
import { CitationSrc, GeneratedSection, Sections } from '../../@types/AsyncTaskState';
import { Section } from './Section';


export function hasTable(section: GeneratedSection): boolean {
  return Boolean((section.table && (section.table?.rows?.length ?? 0) > 0 && (section.table?.columns?.length ?? 0) > 0))
}

export const baseMarkdownOptions: MarkdownToJSX.Options = {
  overrides: {
    p: {
      component: (props) => <Typography {...props} />,
      props: { paragraph: true, variant: 'body1' },
    },
    a: {
      component: (props) => <Link {...props} />,
      props: {
        target: '_blank',
        paragraph: true, variant: 'body1', style: {
          color: 'rgba(10, 142, 98, 1)'
        }
      },
    },
  }
}

export const SectionsInner = (props: { sections: Sections, taskId: string, cookieUserId: string }): React.ReactNode => {
  const { sections, taskId, cookieUserId } = props;
  const [expanded, setExpanded] = React.useState<Set<number>>(new Set<number>([0]));

  const handleOnChange = useCallback((idx: number, isExpanded: boolean) => {
    if (isExpanded) {
      setExpanded(old => {
        return new Set<number>([...old, idx])
      })
    } else {
      setExpanded(old => {
        const newExpanded = new Set<number>([...old])
        if (newExpanded.has(idx)) {
          newExpanded.delete(idx)
        }
        return newExpanded
      })
    }
  }, [setExpanded]);

  const seen = new Set<number>();
  const citations = sections.filter(section => section.text && section.citations).map(section => section.citations).flat().filter(citation => citation && citation?.paper && citation?.id);

  const referencesMarkdown = citations.map((citation) => {
    if (!citation || !citation?.id) {
      return ''
    }
    if (seen.has(citation.paper.corpus_id)) {
      return '';
    }
    seen.add(citation.paper.corpus_id);
    return `1. ${PaperMetadataString({
      authors: citation.paper.authors,
      title: citation.paper.title,
      venue: citation.paper.venue,
      year: citation.paper.year,
      corpusId: citation.paper.corpus_id,
      citationCount: citation.paper.n_citations ?? 0
    }).trim()}`
  }).filter(m => m.length > 0);

  return (
    <>
      <Box>
        {sections.map((section, idx) => {
          if (!section?.text) {
            return null;
          }
          const citationId2Citation: { [corpusId: string]: CitationSrc } = {};

          section.citations?.forEach((citation) => {
            if (citation?.paper?.corpus_id) {
              citationId2Citation[citation.paper.corpus_id] = citation;
            }
          });
          return (
            <AccordionContainer key={`${ section.title } -${ idx } `}>
              <StyledAccordion
                expanded={expanded.has(idx)}
                onChange={(_event, isExpanded) => {
                  handleOnChange(idx, isExpanded);
                }}
                sx={{
                  '& .MuiAccordionSummary-root.Mui-expanded': {
                    height: 'auto !important',
                    minHeight: '0 !important',
                    display: 'flex',
                    alignItems: 'center'
                  }
                }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{
                  padding: '0 16px',
                  alignItems: 'flex-start',
                  position: 'sticky',
                  zIndex: 100,
                  top: 0,
                  background: '#f6f0e9',
                  borderRadius: '8px',
                  '& .MuiAccordionSummary-content': {
                    margin: '16px 0'
                  },
                  '& .MuiAccordionSummary-expandIconWrapper svg': {
                    margin: '12px 0'
                  }
                }}>
                  <Box>
                    <Typography variant="h5" component="h5" color="primary" sx={{
                      padding: '0', display: 'flex', alignItems: 'center'
                    }}>
                      {`${section.title}`}
                      {/* {hasTable(section) ? <ViewListOutlinedIcon fontSize='small' sx={{ marginLeft: '6px' }} /> : null} */}
                    </Typography>
                    {section.tldr && !expanded.has(idx) && (
                      <Typography variant="body1" component="p" sx={{ marginTop: '4px' }}>
                        {`${ section.tldr }`}
                      </Typography>
                    )}
                  </Box>
                </AccordionSummary>
                <Section section={section} idx={idx} taskId={taskId} cookieUserId={cookieUserId} />
              </StyledAccordion>
            </AccordionContainer>
          );
        })}
        <AccordionContainer sx={{ display: referencesMarkdown.length > 0 ? 'block' : 'none' }}>
          <StyledAccordion
            expanded={expanded.has(sections.length)}
            onChange={(_event, isExpanded) => {
              handleOnChange(sections.length, isExpanded);
            }}
            sx={{
              '& .MuiAccordionSummary-root.Mui-expanded': {
                height: 'auto !important',
                minHeight: '0 !important',
                display: 'flex',
                alignItems: 'center'
              }
            }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{
              padding: '0 16px',
              alignItems: 'flex-start',
              position: 'sticky',
              zIndex: 100,
              top: 0,
              borderRadius: '8px',
              background: '#f6f0e9',
              '& .MuiAccordionSummary-content': {
                margin: '16px 0'
              },
              '& .MuiAccordionSummary-expandIconWrapper svg': {
                margin: '12px 0'
              }
            }}>
              <Box>
                <Typography variant="h5" component="h5" color="primary" sx={{
                  padding: '0'
                }}>
                  References
                </Typography>
                {!expanded.has(sections.length) && (
                  <Typography variant="body1" component="p" sx={{ marginTop: '4px' }}>
                    {`${seen.size} paper${seen.size > 1 ? 's' : ''} cited in this answer.`}
                  </Typography>
                )}
              </Box>
            </AccordionSummary>

            <AccordionDetails sx={{
              padding: '0 16px 8px 16px'
            }}>

              <Box sx={{ background: 'white', borderRadius: '4px', padding: '16px 16px 1px 16px', marginBottom: '8px' }}>
                <Markdown options={baseMarkdownOptions}>
                  {referencesMarkdown.join('\n')}
                </Markdown>
              </Box>
            </AccordionDetails>
          </StyledAccordion>
        </AccordionContainer>
      </Box>
    </>
  );
};

const StyledAccordion = styled(Accordion)`
  background: #f7f0e8;
`;

export const FeedbackContainer = styled('div')`
  align-items: center;
  background: #fff;
  border-top: 1px solid rgba(10, 50, 53, 0.1);
  border-radius: 0 0 4px 4px;
  color: rgba(10, 50, 53, 0.8);
  display: flex;
  font-style: italic;
  gap: 12px;
  padding: 16px;
  margin-bottom: 8px;
`;

const AccordionContainer = styled('div')`
  margin-bottom: 8px;
`;
