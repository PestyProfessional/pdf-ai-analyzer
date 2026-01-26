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
        p: 8,
        textAlign: 'center',
        border: dragActive ? '2px dashed #ffffff' : '2px dashed #404855',
        borderRadius: 3,
        bgcolor: dragActive ? 'rgba(255, 255, 255, 0.1)' : 'rgba(64, 72, 85, 0.8)',
        transition: 'all 0.3s ease',
        cursor: 'pointer',
        backdropFilter: 'blur(10px)',
        '&:hover': {
          borderColor: '#ffffff',
          bgcolor: 'rgba(255, 255, 255, 0.05)',
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
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
      
      <Box sx={{ mb: 4 }}>
        {dragActive ? (
          <CloudUpload sx={{ fontSize: 72, color: '#ffffff', opacity: 0.9 }} />
        ) : (
          <PictureAsPdf sx={{ fontSize: 72, color: '#ffffff', opacity: 0.7 }} />
        )}
      </Box>

      <Typography variant="h4" sx={{ mb: 3, color: '#ffffff', fontWeight: 500 }}>
        Spør om hva som helst
      </Typography>

      <Typography variant="body1" sx={{ mb: 4, color: 'rgba(255, 255, 255, 0.7)', fontSize: '1.1rem' }}>
        Dra og slipp PDF-filen her eller klikk for å velge
      </Typography>

      <Button
        variant="outlined"
        size="large"
        startIcon={<CloudUpload />}
        onClick={() => document.getElementById('file-upload').click()}
        sx={{ 
          mb: 4,
          color: '#ffffff',
          borderColor: 'rgba(255, 255, 255, 0.5)',
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          '&:hover': {
            borderColor: '#ffffff',
            backgroundColor: 'rgba(255, 255, 255, 0.2)'
          }
        }}
      >
        Velg dokument
      </Button>

      <Box sx={{ mb: 2 }}>
        <Chip 
          icon={<PictureAsPdf />} 
          label="PDF" 
          size="small" 
          sx={{ 
            mr: 1,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.3)'
          }} 
        />
        <Chip 
          label="Maks 10MB" 
          size="small" 
          variant="outlined"
          sx={{
            color: 'rgba(255, 255, 255, 0.7)',
            borderColor: 'rgba(255, 255, 255, 0.3)'
          }}
        />
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mt: 2,
            backgroundColor: 'rgba(244, 67, 54, 0.1)',
            color: '#ff6b6b',
            border: '1px solid rgba(244, 67, 54, 0.3)'
          }}
        >
          {error}
        </Alert>
      )}

      <Typography 
        variant="caption" 
        sx={{ 
          display: 'block', 
          mt: 3, 
          color: 'rgba(255, 255, 255, 0.5)',
          fontSize: '0.9rem'
        }}
      >
        Dine dokumenter behandles sikkert og slettes automatisk etter analyse
      </Typography>
    </Paper>
  );
};

export default DocumentUpload;