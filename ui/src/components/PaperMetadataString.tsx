import { Author } from "../@types/AsyncTaskState";

export interface PropType {
  authors: Author[];
  year: number;
  venue: string | null;
  maxAuthors?: number;
  title: string;
  corpusId: number | string;
  citationCount: number;
}

export const PaperMetadataString = (props: PropType): string => {
  const { authors: allAuthors, title, year, venue, maxAuthors = 6, corpusId, citationCount } = props;
  const authors = allAuthors.slice(0, maxAuthors);
  const truncated = allAuthors.length > maxAuthors;


  let cleanVenue = ''
  if (venue) {
    cleanVenue = venue.replaceAll('&amp;', '&').replace('&nbsp;', ' ').trim()
    cleanVenue = ` ${cleanVenue}.`
  }

  return (
      `${authors.map((author, index) => {
        return (`<a key="${author.authorId}" target='_blank' href="https://www.semanticscholar.org/author/${author.authorId}">${author.name}</a>${index < authors.length - 1 ? ', ' : ''}`)
      }).join('')}${truncated ? ' et al' : ''}. <a target='_blank' href="https://www.semanticscholar.org/p/${corpusId}">${title}</a>. ${year}.${cleanVenue}${citationCount > 0 ? ` ${citationCount} citations.` : ''}`
  );
};
