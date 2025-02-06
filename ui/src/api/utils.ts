import { CookieSetOptions } from "universal-cookie";
import { AsyncTaskState, GeneratedSection } from "../@types/AsyncTaskState";
import { Feedback, SectionFeedbackMetadata } from "../@types/Feedback";
// import mockTableData2 from "./MockTableData";

export const BACKEND_ENDPOINT = '/api/query_corpusqa'
export const BACKEND_DEFAULT_INIT = {
  headers: {
    'accept': 'application/json',
    'Content-Type': 'application/json',
  },
  method: 'POST'
}
export const FEEDBACK_ENDPOINTS = {
  feedback: '/api/feedback',
  reaction: '/api/reaction',
}
export interface UpdateType {
  update: AsyncTaskState;
  httpStatus: number;
}

const formatSection = (section: GeneratedSection): GeneratedSection => {
  let taggedText = section.text;
  section.citations?.forEach((citation) => {
    if (!citation.id) {
      return;
    }
    const tag = `<Paper id="${citation.id}" corpusId="${citation.paper.corpus_id}" paperTitle="${citation.id}" fullTitle="${citation.paper.title}" />`
    taggedText = taggedText?.replaceAll(citation.id, tag)
    taggedText = taggedText?.replaceAll(" <Paper id=", "<Paper id=")
  })

  return {
    ...section,
    text: taggedText,
    // table: Math.random() > 0.5 ? mockTableData2 : undefined
  }
}

export const formatStatus = (status: AsyncTaskState): AsyncTaskState => {
  if (!status.task_result) {
    return status;
  }
  return {
    ...status,
    task_result: {
      ...status.task_result,
      sections: status.task_result.sections.map(formatSection)
    }
  }
}

export const updateStatus = async (taskId: string): Promise<UpdateType> => {
  const response = await fetch(BACKEND_ENDPOINT, {
    ...BACKEND_DEFAULT_INIT,
    body: JSON.stringify({
      task_id: taskId,
    })
  });
  const output = await response.json() as unknown as AsyncTaskState;
  return { update: formatStatus(output), httpStatus: response.status };
}

export const sendReaction = async (
  taskId: string,
  userId: string,
  reaction: '+1' | '-1' | undefined,
  section: SectionFeedbackMetadata | null
): Promise<any> => {
  const feedback: Feedback = {
    msg_id: taskId,
    user_id: userId,
    feedback: reaction,
    section
  }
  if (!reaction) {
    delete feedback.feedback;
  }
  if (!section) {
    delete feedback.section;
  }
  const response = await fetch(FEEDBACK_ENDPOINTS.reaction, {
    ...BACKEND_DEFAULT_INIT,
    body: JSON.stringify(
      feedback
    )
  });
  if(!response.ok) {
    throw new Error("Not implemented");
  }
  const output = await response.json();
  return output;
}

export const sendFeedback= async (
  taskId: string,
  userId: string,
  text: string, 
  section: SectionFeedbackMetadata | null
): Promise<any> => {
  const feedback: Feedback = {
    msg_id: taskId,
    user_id: userId,
    feedback: text,
    section
  }
  if (!section) {
    delete feedback.section;
  }
  const response = await fetch(FEEDBACK_ENDPOINTS.feedback, {
    ...BACKEND_DEFAULT_INIT,
    body: JSON.stringify(
      feedback
    )
  });
  if(!response.ok) {
    throw new Error("Not implemented");
  }

  const output = await response.json();
  return output;

}

export const createTask = async (query: string, optin: boolean, userId: string) => {
  const response = await fetch(BACKEND_ENDPOINT, {
    ...BACKEND_DEFAULT_INIT,
    body: JSON.stringify({
      query,
      opt_in: optin,
      user_id: userId,
      feedback_toggle: true
    })
  })
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json() as unknown as AsyncTaskState;
}

export interface Evidence {
  // bboxs?: BoundingBox[];
  heading?: string;
  text: string;
}

export function getEvidence(evidenceId: number) {
  return fetch(`https://s2-labs-paper-qa.allen.ai/api/QAData/${evidenceId}`).then(
    (response) =>
      response.json() as unknown as {
        supports: Evidence[];
        corpusId: number;
      },
  );
}

export const COOKIES_SET_OPTIONS: CookieSetOptions  = { path: '/', expires: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30 * 1200) }