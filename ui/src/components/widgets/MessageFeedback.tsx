import React from 'react';

import CancelIcon from '@mui/icons-material/Cancel';
import Paper from '@mui/material/Paper';
import Popper from '@mui/material/Popper';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';
import {
  Box,
  Button,
  ClickAwayListener,
  Snackbar,
  TextField,
  Typography,
  styled,
} from '@mui/material';
import { SectionFeedbackMetadata } from '../../@types/Feedback';
import { sendFeedback, sendReaction } from '../../api/utils';

enum FeedbackTitle {
  THUMBS_UP = 'Any additional comments on why it is helpful? (optional) ',
  THUMBS_DOWN = 'Any additional comments on what went wrong? (optional) ',
  FEEDBACK = 'General feedback or suggestions.',
}

interface Props {
  taskId: string;
  userId: string;
  section: SectionFeedbackMetadata | null;
  darkMode?: boolean
}

export const MessageFeedbackComp: React.FC<Props> = (props) => {
  const { taskId, userId, section = null, darkMode = false } = props;
  const [isFeedbackFormOpen, setIsFeedbackFormOpen] = React.useState(false);
  const [feedbackFormAnchorEl, setFeedbackFormAnchorEl] =
    React.useState<Element | null>(null);
  const [feedbackFormState, setFeedbackFormState] = React.useState({
    text: '',
    isSaving: false,
    errorMessage: '',
  });
  const [feedbackTitle, setFeedbackTitle] = React.useState('');
  const [thumbs, setThumbs] = React.useState<'unset' | '+1' | '-1'>('unset');
  const [openThanks, setOpenThanks] = React.useState(false);
  const handleCloseThanks = React.useCallback(() => {
    setOpenThanks(false);
  },[setOpenThanks])
  const [snackMessage, setSnackMessage] = React.useState<string>('Thanks for your feedback!');

  const onClickThumbsUp: React.MouseEventHandler = (event) => {
    setFeedbackTitle(FeedbackTitle.THUMBS_UP);
    setFeedbackFormAnchorEl(event.currentTarget);
    setIsFeedbackFormOpen(true);
    try {
      sendReaction(taskId, userId, '+1', section);
      setThumbs('+1');
      setSnackMessage('Thanks for your feedback!');
    } catch (error) {
      setSnackMessage('Feedback is not implemented in this version.');
    }
  };

  const onClickThumbsDown: React.MouseEventHandler = (event) => {
    setFeedbackTitle(FeedbackTitle.THUMBS_DOWN);
    setFeedbackFormAnchorEl(event.currentTarget);
    setIsFeedbackFormOpen(true);
    try {
      sendReaction(taskId, userId, '-1', section);
      setThumbs('-1');
      setSnackMessage('Thanks for your feedback!');
    } catch (error) {
      setSnackMessage('Feedback is not implemented in this version.');
    }
  };

  const onClickFeedback: React.MouseEventHandler = (event) => {
    setFeedbackTitle(FeedbackTitle.FEEDBACK);
    setFeedbackFormAnchorEl(event.currentTarget);
    setIsFeedbackFormOpen(true);
  };

  const onCloseFeedbackForm = () => {
    setIsFeedbackFormOpen(false);
  };

  const onChangeFeedbackText: React.ChangeEventHandler<HTMLInputElement> = (
    event,
  ) => {
    setFeedbackFormState({
      ...feedbackFormState,
      text: event.target.value,
    });
  };

  const onClickSubmitFeedback: React.MouseEventHandler = () => {
    const feedback = feedbackFormState.text.trim();
    if (!feedback) {
      // Don't submit empty feedback
      return;
    }

    setFeedbackFormState({
      ...feedbackFormState,
      isSaving: true,
      errorMessage: '',
    });
    try {
      sendFeedback(taskId, userId, feedback, section);
      setSnackMessage('Thanks for your feedback!');
    } catch (error) {
      setSnackMessage('Feedback is not implemented in this version.');
    }
    setIsFeedbackFormOpen(false);
    setOpenThanks(true);

    setFeedbackFormState({
      ...feedbackFormState,
      isSaving: false,
      text: '',
      errorMessage: '',
    });
  };

  return (
    <ButtonRow>
      <ThumbsUpBtn
        isSelected={thumbs === '+1'}
        sx={{ color: darkMode ? 'white' : 'black' }}
        onClick={onClickThumbsUp}
      />
      <ThumbsDownBtn
        isSelected={thumbs === '-1'}
        sx={{ color: darkMode ? 'white' : 'black' }}
        onClick={onClickThumbsDown}
      />
      <FeedbackBtn
        sx={{ color: darkMode ? 'white' : 'black' }}
        onClick={onClickFeedback}
      />
      <Popper
        sx={{ zIndex: 100000 }}
        open={isFeedbackFormOpen}
        anchorEl={feedbackFormAnchorEl}
        data-testid="message-feedback-modal"
        placement="bottom"
        disablePortal={false}
        modifiers={[
          {
            name: 'flip',
            enabled: true,
            options: {
              altBoundary: true,
              rootBoundary: 'document',
              padding: 8,
            },
          },
          {
            name: 'preventOverflow',
            enabled: true,
            options: {
              altAxis: true,
              altBoundary: true,
              tether: true,
              rootBoundary: 'document',
              padding: 8,
            },
          },
        ]}
      >
        <ClickAwayListener onClickAway={onCloseFeedbackForm}>
          <Paper
            sx={{
              maxWidth: '480px',
              padding: '16px',
              backgroundColor: '#08232b',
              color: '#FAF2E9'
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <Typography variant="h6">{feedbackTitle}</Typography>
              <CloseBtn onClick={onCloseFeedbackForm} />
            </Box>

            <TextField
              fullWidth
              multiline
              placeholder="Feedback"
              disabled={feedbackFormState.isSaving}
              value={feedbackFormState.text}
              onChange={onChangeFeedbackText}
              rows={2}
              variant="outlined"
              sx={{
                border: '1px solid rgba(255, 240, 243, 0.6)',
                marginBottom: `12px`,
                borderRadius: '4px',
                '& .MuiInputBase-input':{
                  color: '#FAF2E9 !important',
                }
              }}
            />

              {feedbackFormState.errorMessage && (
                <Typography
                  align="left"
                  color="error"
                  data-testid="message-error"
                  variant="body2"
                >
                  Error submitting feedback, please try again.
                </Typography>
              )}
              <Button
                variant="contained"
                size="small"
                data-testid="message-feedback-submit-button"
                color="secondary"
                disabled={feedbackFormState.isSaving}
                onClick={onClickSubmitFeedback}
              >
                Submit
              </Button>

          </Paper>
        </ClickAwayListener>
      </Popper>
      <Snackbar
        open={openThanks}
        autoHideDuration={2000}
        onClose={handleCloseThanks}
        message="Thanks for your feedback!"
      />
    </ButtonRow>
  );
};

// const mapStateToProps = (state: RootState) => ({
//   currentUser: state.userStore.currentUser,
// });

// export const MessageFeedback = connect(mapStateToProps)(MessageFeedbackComp);

const ButtonRow = styled('div')`
  display: flex;
  gap: ${({ theme }) => theme.spacing(1)};
`;

const ReactionBtn = styled('button')`
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.3;
  padding: 0;
  transition: opacity 250ms ease-in-out;
  color: ${({ theme }) => theme.palette.text.primary};

  &:hover {
    opacity: 0.7;
    transition-duration: 75ms;
  }

  &:active {
    opacity: 1;
    transition-duration: 0ms;
  }
`;

type ReactionBtnProps = React.ComponentProps<typeof ReactionBtn> & {
  isSelected?: boolean;
};

export const ThumbsUpBtn = ({ isSelected, ...props }: ReactionBtnProps) => {
  return (
    <ReactionBtn {...props} data-testid="message-reaction-thumbs-up">
      {isSelected ? (
        <ThumbUpIcon fontSize="small" />
      ) : (
        <ThumbUpOutlinedIcon fontSize="small" />
      )}
    </ReactionBtn>
  );
};

export const ThumbsDownBtn = ({ isSelected, ...props }: ReactionBtnProps) => {
  return (
    <ReactionBtn {...props} data-testid="message-reaction-thumbs-down">
      {isSelected ? (
        <ThumbDownIcon fontSize="small" />
      ) : (
        <ThumbDownOutlinedIcon fontSize="small" />
      )}
    </ReactionBtn>
  );
};

export const FeedbackBtn = ({ ...props }: ReactionBtnProps) => {
  return (
    <ReactionBtn {...props} data-testid="message-reaction-feedback">
      <ChatBubbleOutlineIcon fontSize="small" />
    </ReactionBtn>
  );
};


export const CloseBtn = (props: React.ComponentProps<typeof ReactionBtn>) => {
  return (
    <ReactionBtn {...props}>
      <CancelIcon fontSize="small" color="secondary" />
    </ReactionBtn>
  );
};
