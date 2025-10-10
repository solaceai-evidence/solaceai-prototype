import * as React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/AddBoxOutlined';
import Drawer from '@mui/material/Drawer';
import DeleteIcon from '@mui/icons-material/Delete';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import { historyType } from './shared';
import { useLocation, useNavigate } from 'react-router-dom';
import { useCallback } from 'react';
import { IconButton } from '@mui/material';

interface PropType {
  mobileOpen: boolean;
  handleDrawerTransitionEnd: () => void;
  handleDrawerClose: () => void;
  drawerWidth: number;
  history: historyType;
  setHistory: (history: historyType) => void;
}

export const Sidebar: React.FC<PropType> = (props) => {
  const {
    mobileOpen,
    handleDrawerTransitionEnd,
    handleDrawerClose,
    drawerWidth,
    history,
    setHistory,
  } = props;
  const location = useLocation();
  const navigate = useNavigate();
  console.log('sidebar history', history);

  const sortedHistory = Object.values(history ?? {}).sort((a, b) => b.timestamp - a.timestamp);

  const handleDeleteTask = useCallback(
    (event: React.MouseEvent, taskId: string) => {
      event.preventDefault();
      event.stopPropagation();
      if (confirm('Are you sure you want to delete this? This cannot be undone.')) {
        const newHistory = { ...(history ?? {}) };
        navigate('/');
        try {
          delete newHistory[taskId];
          console.log('deleted history', newHistory);
          setHistory(newHistory ?? {});
          navigate('/');
        } catch (e) {
          console.error('delete task failed', e);
        }
      }
    },
    [history, setHistory, navigate]
  );

  const drawer = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: { xs: '100vh', sm: '100%' },
        backgroundColor: (theme) => theme.palette.background.default,
        color: (theme) => theme.palette.text.primary,
      }}
    >
      <Box sx={{ borderBottom: '1px solid rgba(250, 242, 233, 0.1)' }}>
        <Button
          href="/"
          variant="text"
          sx={{
            display: 'flex',
            justifyContent: 'flex-start',
            lineHeight: '40px',
            padding: '8px 18px',
          }}
          startIcon={<AddIcon />}
          color="secondary"
          size="large"
        >
          Ask A New Question
        </Button>
      </Box>

      <Typography variant="h6" sx={{ margin: '16px 18px 0 18px', fontWeight: 'bold' }}>
        Recent Questions
      </Typography>
      <List
        sx={{
          overflow: 'auto',
          flexGrow: '1',
        }}
      >
        {sortedHistory.map((item) => {
          const selected = location.pathname.includes(item.taskId);
          return (
            <ListItem key={item.taskId} sx={{ padding: '0 4px' }}>
              <ListItemButton
                selected={selected}
                sx={{
                  padding: '2px 6px 2px 14px',
                  backgroundColor: selected
                    ? 'rgba(250, 242, 233, 0.04) !important'
                    : 'transparent',
                  borderRadius: '4px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '4px',
                  '&:hover': { backgroundColor: 'rgba(250, 242, 233, 0.06)' },
                }}
                onClick={() => {
                  navigate(`/query/${item.taskId}`, { replace: true });
                }}
              >
                <Typography
                  sx={{
                    fontSize: '14px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    lineHeight: `36px`,
                  }}
                >
                  {item.query}
                </Typography>
                {selected && (
                  <IconButton
                    aria-label="delete"
                    size="small"
                    onClick={(event) => handleDeleteTask(event, item.taskId)}
                    sx={{ padding: '4px' }}
                  >
                    <DeleteIcon
                      fontSize="small"
                      sx={{
                        fill: '#F8F0E7',
                        '&:hover': { fill: '#F0529C' },
                      }}
                    />
                  </IconButton>
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ padding: '18px', borderTop: '1px solid rgba(250, 242, 233, 0.1)' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', paddingBottom: '4px' }}>
          <Link href="https://www.semanticscholar.org" target="_blank">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 557.7 100">
              <path
                fill="#F8F0E7"
                d="M179.4,40.5c-.1.2-.2.4-.4.5-.2.1-.4.2-.6.2-.3,0-.6-.1-.8-.3-.3-.2-.7-.5-1.2-.7-.5-.3-1.1-.6-1.7-.8-.7-.2-1.5-.3-2.3-.3-.8,0-1.5,0-2.2.3-.6.2-1.1.5-1.6.9-.4.4-.8.8-1,1.3-.2.5-.3,1.1-.3,1.7,0,.7.2,1.4.6,1.9.4.5,1,1,1.6,1.3.7.4,1.4.7,2.2,1l2.5.8c.9.3,1.7.6,2.5,1,.8.4,1.5.8,2.2,1.4.7.6,1.2,1.3,1.6,2.1.4.9.6,2,.6,3,0,1.2-.2,2.4-.6,3.6-.4,1.1-1.1,2.1-1.9,2.9-.9.9-1.9,1.6-3.1,2-1.3.5-2.7.7-4.1.7-1.8,0-3.5-.3-5.2-1-.8-.3-1.5-.7-2.2-1.2-.7-.5-1.3-1-1.8-1.6l1.2-2c.1-.2.3-.3.4-.4.2-.1.4-.2.6-.2.4,0,.7.2,1,.5.4.3.8.6,1.4,1,.6.4,1.3.7,2,1,.9.3,1.8.5,2.8.4.8,0,1.6-.1,2.4-.3.7-.2,1.3-.5,1.8-1,.5-.4.9-1,1.1-1.6.3-.7.4-1.3.4-2,0-.7-.2-1.5-.6-2.1-.4-.6-1-1.1-1.6-1.5-.7-.4-1.4-.7-2.2-.9l-2.5-.8c-.9-.3-1.7-.6-2.5-1-.8-.3-1.5-.8-2.2-1.4-.7-.6-1.2-1.4-1.6-2.2-.4-1-.6-2.1-.6-3.3,0-2.1.8-4.1,2.4-5.6.8-.8,1.8-1.4,2.9-1.8,1.2-.5,2.5-.7,3.9-.7,1.5,0,3,.2,4.5.8,1.3.5,2.5,1.3,3.6,2.2l-1,2.1Z"
              />
              <path
                fill="#F8F0E7"
                d="M203.7,61.2v3.5h-17.9v-28.9h17.9v3.5h-13.6v9.2h11v3.4h-11v9.4h13.7Z"
              />
              <path
                fill="#F8F0E7"
                d="M238.2,35.8v28.9h-3.7v-21.6c0-.3,0-.7,0-1.1l-9.6,17.7c-.3.6-.9,1-1.6,1h-.6c-.7,0-1.3-.4-1.5-1l-9.8-17.7c0,.7.1,1.4.1,2.1v20.6h-3.8v-28.9h3.2c.3,0,.6,0,.9.1.3.1.5.3.6.6l9.7,17.3c.2.3.4.7.5,1.1s.3.8.5,1.2c.3-.8.6-1.5,1-2.3l9.5-17.3c.1-.3.3-.5.6-.6.3,0,.6-.1.9-.1h3.2Z"
              />
              <path
                fill="#F8F0E7"
                d="M268.7,64.7h-3.3c-.3,0-.7,0-.9-.3-.2-.2-.4-.4-.5-.7l-2.6-6.7h-12.8l-2.6,6.7c-.1.3-.3.5-.5.7-.3.2-.6.3-.9.3h-3.3l11.5-28.9h4.3l11.5,28.9ZM260.2,53.9l-4.3-11.2c-.4-1-.7-1.9-.9-2.9-.1.6-.3,1.1-.4,1.6s-.3.9-.4,1.3l-4.3,11.2h10.4Z"
              />
              <path
                fill="#F8F0E7"
                d="M295.5,35.8v28.9h-2.2c-.3,0-.6,0-.8-.2-.3-.2-.5-.4-.7-.6l-16.3-21.1c0,.4,0,.7,0,1.1s0,.7,0,1v19.8h-3.8v-28.9h2.2c.3,0,.6,0,.9.1.3.1.5.3.6.6l16.4,21.2c0-.4,0-.8,0-1.1v-20.7h3.8Z"
              />
              <path fill="#F8F0E7" d="M321.6,39.3h-9.2v25.3h-4.3v-25.3h-9.2v-3.6h22.7v3.6Z" />
              <path fill="#F8F0E7" d="M329.3,64.7h-4.3v-28.9h4.3v28.9Z" />
              <path
                fill="#F8F0E7"
                d="M356.2,58.5c.2,0,.5.1.6.3l1.7,1.9c-1.2,1.4-2.7,2.5-4.3,3.2-1.9.8-4,1.2-6.1,1.1-2,0-3.9-.3-5.7-1.1-1.6-.7-3.1-1.7-4.4-3-1.2-1.3-2.2-2.9-2.8-4.7-.7-1.9-1-4-1-6,0-2,.3-4.1,1-6,.6-1.7,1.6-3.3,2.9-4.7,1.3-1.3,2.8-2.3,4.5-3,1.8-.7,3.8-1.1,5.8-1.1,1.9,0,3.7.3,5.5,1,1.5.6,3,1.5,4.2,2.7l-1.4,2c0,.1-.2.3-.4.4-.2,0-.4.1-.5.1-.3,0-.6-.2-.9-.4-.4-.3-.9-.6-1.4-.9-.7-.4-1.4-.6-2.1-.9-1-.3-2-.4-3.1-.4-1.4,0-2.7.2-4,.8-1.2.5-2.2,1.2-3.1,2.2-.9,1-1.6,2.2-2,3.5-.5,1.5-.7,3.1-.7,4.7,0,1.6.2,3.2.8,4.7.4,1.3,1.1,2.5,2,3.5.9.9,1.9,1.7,3.1,2.2,1.2.5,2.5.7,3.8.7.8,0,1.5,0,2.2-.2.6,0,1.2-.2,1.8-.5.6-.2,1.1-.5,1.6-.8.5-.3,1-.7,1.5-1.1.1,0,.2-.2.4-.2.1,0,.3-.1.5-.1Z"
              />
              <path
                fill="#F8F0E7"
                d="M388.7,41.3c-.2.3-.4.5-.7.7-.3.2-.5.3-.9.2-.4,0-.7-.1-1-.3l-1.1-.6c-.5-.3-1-.5-1.5-.7-.6-.2-1.3-.3-2-.3-1,0-2,.2-2.9.8-.6.6-1,1.4-.9,2.2,0,.5.2,1.1.6,1.5.4.4.9.8,1.5,1,.7.3,1.4.6,2.1.8.8.2,1.6.5,2.4.8.8.3,1.6.6,2.4,1,.8.4,1.5.9,2.1,1.5.6.6,1.1,1.4,1.5,2.2.4,1,.6,2.1.6,3.1,0,1.3-.2,2.6-.7,3.8-.5,1.2-1.2,2.2-2.1,3.1-.9.9-2.1,1.6-3.3,2.1-1.4.5-2.9.8-4.5.8-.9,0-1.9,0-2.8-.3-.9-.2-1.9-.5-2.7-.8-.9-.3-1.7-.7-2.5-1.2-.7-.4-1.4-1-2-1.6l2-3.2c.2-.2.4-.4.6-.6.3-.2.6-.2.9-.2.4,0,.9.1,1.2.4l1.4.8c.6.3,1.2.6,1.8.8.8.3,1.6.4,2.4.4,1,0,2-.2,2.9-.8.7-.7,1.1-1.6,1-2.6,0-.6-.2-1.2-.6-1.7-.4-.5-.9-.8-1.5-1.1-.7-.3-1.4-.6-2.1-.8-.8-.2-1.6-.5-2.4-.7-.8-.3-1.6-.6-2.4-1-.8-.4-1.5-.9-2.1-1.5-.6-.7-1.1-1.5-1.5-2.3-.4-1.1-.6-2.3-.6-3.5,0-1.1.3-2.2.7-3.2.5-1.1,1.1-2,2-2.8.9-.9,2-1.5,3.2-2,1.4-.5,2.8-.8,4.3-.7.9,0,1.8,0,2.6.2,1.6.3,3.2.8,4.6,1.6.6.4,1.2.8,1.8,1.3l-1.8,3.2Z"
              />
              <path
                fill="#F8F0E7"
                d="M414,57.1c.4,0,.7.1,1,.4l2.7,2.8c-1.2,1.5-2.7,2.7-4.4,3.5-2,.8-4.2,1.2-6.3,1.2-2.1,0-4.1-.4-6-1.1-1.7-.7-3.2-1.8-4.5-3.1-1.2-1.4-2.2-3-2.8-4.7-.7-1.9-1-4-1-6,0-2,.3-4.1,1.1-6,.7-1.8,1.7-3.4,3-4.8,1.3-1.3,2.9-2.4,4.6-3.1,1.9-.8,3.9-1.2,5.9-1.2,1,0,2.1,0,3.1.3.9.2,1.8.5,2.7.8,1.6.6,3,1.6,4.2,2.8l-2.3,3.1c-.2.2-.3.4-.5.5-.2.2-.5.3-.8.2-.2,0-.5,0-.7-.2-.2-.1-.5-.3-.7-.4l-.8-.5c-.3-.2-.7-.4-1-.5-.5-.2-.9-.3-1.4-.4-.6-.1-1.2-.2-1.9-.2-1.1,0-2.1.2-3.1.6-.9.4-1.8,1-2.4,1.8-.7.9-1.3,1.9-1.6,2.9-.4,1.3-.6,2.6-.6,4,0,1.4.2,2.7.6,4,.4,1.1.9,2.1,1.7,3,.7.8,1.5,1.4,2.5,1.8.9.4,2,.6,3,.6.6,0,1.1,0,1.7,0,.5,0,1-.2,1.4-.3.4-.1.9-.3,1.2-.6.4-.3.8-.6,1.2-.9.2-.1.3-.3.5-.3.2-.1.4-.2.6-.2Z"
              />
              <path
                fill="#F8F0E7"
                d="M445.6,35.3v29.4h-6.9v-12.4h-11.9v12.4h-6.8v-29.4h6.9v12.3h11.9v-12.3h6.8Z"
              />
              <path
                fill="#F8F0E7"
                d="M479.8,50c0,2-.4,4-1.1,5.9-.7,1.8-1.8,3.4-3.1,4.8-1.4,1.4-3,2.5-4.8,3.2-4,1.5-8.5,1.5-12.5,0-3.6-1.4-6.5-4.3-7.9-7.9-1.5-3.8-1.5-8,0-11.8.7-1.8,1.8-3.4,3.1-4.8,1.4-1.4,3-2.4,4.8-3.2,4-1.5,8.5-1.5,12.5,0,1.8.7,3.4,1.8,4.8,3.2,1.3,1.4,2.4,3,3.1,4.8.7,1.9,1.1,3.9,1.1,5.9ZM472.8,50c0-1.3-.2-2.7-.6-3.9-.3-1.1-.9-2.1-1.6-3-.7-.8-1.6-1.4-2.6-1.8-1.1-.4-2.3-.7-3.5-.7-1.2,0-2.4.2-3.5.7-1,.4-1.9,1-2.6,1.8-.7.9-1.3,1.9-1.6,3-.8,2.6-.8,5.3,0,7.9.3,1.1.9,2.1,1.6,3,.7.8,1.6,1.4,2.6,1.8,1.1.4,2.3.7,3.5.6,1.2,0,2.4-.2,3.5-.6,1-.4,1.9-1,2.6-1.8.7-.9,1.3-1.9,1.6-3,.4-1.3.6-2.6.6-4h0Z"
              />
              <path fill="#F8F0E7" d="M501.1,59.2v5.4h-17.7v-29.4h6.8v23.9h10.9Z" />
              <path
                fill="#F8F0E7"
                d="M531.7,64.7h-5.3c-.5,0-1-.1-1.4-.4-.4-.3-.6-.6-.8-1l-1.7-5.1h-11.2l-1.7,5.1c-.2.4-.4.7-.8,1-.4.3-.9.5-1.4.5h-5.3l11.4-29.4h7l11.3,29.4ZM520.9,53.5l-2.7-8c-.2-.5-.4-1.1-.7-1.8s-.5-1.4-.7-2.2c-.2.8-.4,1.6-.7,2.3s-.4,1.3-.6,1.8l-2.7,8h8Z"
              />
              <path
                fill="#F8F0E7"
                d="M557.7,64.7h-6.2c-1,0-2-.4-2.5-1.3l-4.9-8.5c-.2-.3-.5-.6-.8-.8-.4-.2-.8-.3-1.2-.2h-1.7v10.9h-6.8v-29.4h9.5c1.8,0,3.7.2,5.4.7,1.3.3,2.6,1,3.7,1.8.9.7,1.6,1.7,2.1,2.8.4,1.1.7,2.3.7,3.4,0,.9-.1,1.8-.4,2.7-.5,1.7-1.6,3.2-3,4.3-.8.6-1.6,1-2.5,1.4.4.2.9.5,1.2.8.4.4.7.8,1,1.2l6.3,10.2ZM543.2,49.1c.8,0,1.6,0,2.4-.3.6-.2,1.1-.5,1.6-1,.4-.4.7-.9.9-1.5.2-.6.3-1.2.3-1.8,0-1.1-.4-2.2-1.3-3-1.1-.8-2.5-1.2-3.9-1.1h-2.7v8.7h2.7Z"
              />
              <path
                fill="#F8F0E7"
                d="M138.6,30.4c-4.9,3.1-8.3,4.8-12.3,7.2-24,14.5-47.1,30.7-65,51.9l-8.6,10.5-26.5-42c5.9,4.7,20.6,17.9,26.6,20.8l19.4-14.5c13.6-9.6,51.7-30.3,66.4-33.9Z"
              />
              <path
                fill="#F8F0E7"
                d="M38.6,61.9l1.9,1.5c-5.8-15.8-15.2-30-27.4-41.6H0c15.3,10.8,28.4,24.4,38.6,40Z"
              />
              <path
                fill="#F8F0E7"
                d="M42.9,65.7l1.6,1.3c-.8-19.7-8.2-39.8-22.1-57.1h-12.4c17.9,16.5,28.8,36.4,32.9,55.8Z"
              />
              <path
                fill="#F8F0E7"
                d="M46.5,68.5c2,1.6,4,3.1,5.6,4.2,4.4-21.9.5-44.6-10.9-63.8l58.4-.8c4.4,9.6,6.9,20,7.5,30.6,1.7-.9,3.4-1.7,5.1-2.5C111.5,25.4,108.5,13.6,102.6,0H22.9c17.3,20.5,25.2,45.3,23.6,68.5Z"
              />
            </svg>
          </Link>
        </Box>
        <Link
          href="https://allenai.org/privacy-policy"
          target="_blank"
          underline="hover"
          variant="body2"
          sx={{ color: '#0FCB8C' }}
        >
          Privacy Policy
        </Link>
        &nbsp;&nbsp;•&nbsp;&nbsp;
        <Link
          href="https://allenai.org/terms"
          target="_blank"
          underline="hover"
          variant="body2"
          sx={{ color: '#0FCB8C' }}
        >
          Terms of Use
        </Link>
        &nbsp;&nbsp;•&nbsp;&nbsp;
        <Link
          href="https://allenai.org/responsible-use"
          target="_blank"
          underline="hover"
          variant="body2"
          sx={{ color: '#0FCB8C' }}
        >
          Responsible Use
        </Link>
        {/* <Link href="https://allenai.org" target="_blank">Ai2</Link> */}
      </Box>
    </Box>
  );

  return (
    <>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onTransitionEnd={handleDrawerTransitionEnd}
        onClose={handleDrawerClose}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          flexShrink: 0,
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            backgroundColor: (theme) => theme.palette.background.default,
            color: (theme) => theme.palette.text.primary,
            width: { xs: '80vw', sm: '240px' },
          },
        }}
      >
        {drawer}
      </Drawer>
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            backgroundColor: (theme) => theme.palette.background.default,
            color: (theme) => theme.palette.text.primary,
            width: { xs: '80vw', sm: '240px' },
          },
        }}
        open
      >
        {drawer}
      </Drawer>
    </>
  );
};
export default Sidebar;
