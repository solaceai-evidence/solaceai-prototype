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
            color: (theme) => theme.palette.primary.main,
            textTransform: 'none',
          }}
          startIcon={<AddIcon />}
          color="inherit"
          size="large"
        >
          Ask a New Question
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
                    fontSize: '1.0rem',
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
