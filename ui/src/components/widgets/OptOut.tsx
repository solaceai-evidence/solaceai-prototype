import * as React from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Link, Typography } from '@mui/material';

interface Props {
  open: boolean;
  onClose: (value: 'yes' | 'no' | 'unset') => void;
}

export const OptOut: React.FC<Props> = (props) => {
  const { onClose, open, ...other } = props;

  const handleCancel = () => {
    onClose('no');
  };

  const handleOk = () => {
    onClose('yes');
  };

  const consentPopover = (
    <Dialog
      sx={{ '& .MuiDialog-paper': { maxHeight: 435 } }}
      maxWidth="sm"
      open={open}
      {...other}
    >
      <DialogTitle sx={{ padding: '24px 24px 8px 24px', fontSize: '18px' }}>Terms of Use and Data Consent</DialogTitle>
      <DialogContent sx={{ borderBottom: '1px solid rgba(10,50,55,0.2)', padding: '24px' }}>
        <DialogContentText id="alert-dialog-description">
          <Typography sx={{ marginBottom: '8px' }}>
            By using Ai2 Scholar QA, you agree to the <Link href="https://allenai.org/terms" target="_blank" sx={{ fontWeight: 'bold' }}>Terms of Use</Link>, <Link href="https://allenai.org/responsible-use" target="_blank" sx={{ fontWeight: 'bold' }} >Responsible Use</Link>, <Link href="https://allenai.org/privacy-policy" target="_blank" sx={{ fontWeight: 'bold' }}>Privacy Policy</Link> and that you will not submit any sensitive or confidential info.
          </Typography>
          <Typography>
            Ai2 may use your queries in a public dataset for future AI research and development. You can still use this tool if you opt-out.
          </Typography>
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ padding: '16px', display:'flex', justifyContent:'space-between' }}>
        <Button onClick={handleCancel} sx={{ color: 'rgba(10,50,55,0.8)' }}>I agree, but opt-out of query collection</Button>
        <Button onClick={handleOk} variant="contained" color="secondary">I agree, and ok to use my queries</Button>
      </DialogActions>
    </Dialog>
  )

  return (
    <>
      {consentPopover}
    </>
  );
}
