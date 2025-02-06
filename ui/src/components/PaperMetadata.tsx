import React from 'react';
import { Link } from '@mui/material';
import { Author } from '../@types/AsyncTaskState';



export interface PropType {
  authors: Author[];
  year: number;
  venue: string | null;
  title: string;
  maxAuthors?: number;
  citationCount: number;
}

export const PaperMetadata: React.FC<PropType> = (props) => {
  const { authors: allAuthors, year, venue, maxAuthors = 6, citationCount } = props;
  const authors = allAuthors.slice(0, maxAuthors);
  const truncated = allAuthors.length > maxAuthors;

  let cleanVenue = ''
  if (venue) {
    cleanVenue = venue.replaceAll('&amp;', '&').replace('&nbsp;', ' ')
    cleanVenue = ` ${cleanVenue}. `
  }

  return (
    <div style={{ display: 'inline-block' }}>
      {authors.map((author, index) => (
        <React.Fragment  key={author.authorId}>
          <Link color='secondary' href={`https://www.semanticscholar.org/author/${author.authorId}`}>{author.name}</Link>
          {index < authors.length - 1 ? ', ' : ''}
        </React.Fragment>
      ))}{truncated ? ' et al' : ''}.{cleanVenue}{year}.{props.citationCount > 0 ? ` ${citationCount} citations.` : ''}
    </div>
  );
};
