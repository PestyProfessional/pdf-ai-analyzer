import React, { useState, useCallback } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  Chip
} from '@mui/material';
import { CloudUpload, PictureAsPdf, Description } from '@mui/icons-material';

const DocumentUpload = ({ onFileSelect }) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');

  const validateFile = (file) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['application/pdf'];
    
    if (!allowedTypes.includes(file.type)) {
      return 'Kun PDF-filer er tillatt';
    }
    
    if (file.size > maxSize) {
      return 'Filen er for stor. Maksimal størrelse er 10MB';
    }
    
    return null;
  };

  const handleFiles = useCallback((files) => {
    const file = files[0];
    if (!file) return;

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    onFileSelect(file);
  }, [onFileSelect]);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleChange = useCallback((e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  return (
    <Paper
      sx={{
        p: 6,
        textAlign: 'center',
        border: dragActive ? '2px dashed #2C5F2D' : '2px dashed #ccc',
        borderRadius: 2,
        bgcolor: dragActive ? '#f3f7f3' : 'white',
        transition: 'all 0.3s ease',
        cursor: 'pointer',
        '&:hover': {
          borderColor: '#2C5F2D',
          bgcolor: '#f8f9fa'
        }
      }}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-upload"
        multiple={false}
        accept="application/pdf"
        onChange={handleChange}
        style={{
          position: 'absolute',
          left: '-9999px'
        }}
      />
      
      <Box sx={{ mb: 3 }}>
        {dragActive ? (
          <CloudUpload sx={{ fontSize: 80, color: 'primary.main' }} />
        ) : (
          <PictureAsPdf sx={{ fontSize: 80, color: 'primary.main' }} />
        )}
      </Box>

      <Typography variant="h5" sx={{ mb: 2, color: 'primary.main' }}>
        Last opp dokumentet for å få en oppsummering
      </Typography>

      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Dra og slipp PDF-filen her eller klikk for å velge
      </Typography>

      <Button
        variant="contained"
        size="large"
        startIcon={<CloudUpload />}
        onClick={() => document.getElementById('file-upload').click()}
        sx={{ mb: 2 }}
      >
        Velg dokument
      </Button>

      <Box sx={{ mb: 2 }}>
        <Chip 
          icon={<PictureAsPdf />} 
          label="PDF" 
          size="small" 
          sx={{ mr: 1 }} 
        />
        <Chip 
          label="Maks 10MB" 
          size="small" 
          variant="outlined" 
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Typography variant="caption" sx={{ display: 'block', mt: 2, color: 'text.secondary' }}>
        Dine dokumenter behandles sikkert og slettes automatisk etter analyse
      </Typography>
    </Paper>
  );
};

export default DocumentUpload;