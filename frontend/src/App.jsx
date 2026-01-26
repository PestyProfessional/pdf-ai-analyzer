import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  LinearProgress,
  Alert
} from '@mui/material';
import { CloudUpload, Description } from '@mui/icons-material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import DocumentUpload from './components/DocumentUpload';
import ResultsDisplay from './components/ResultsDisplay';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2C5F2D',
    },
    secondary: {
      main: '#97BC62',
    },
    background: {
      default: '#13264A',
      paper: 'rgba(255, 255, 255, 0.95)'
    },
  },
  typography: {
    fontFamily: '"Work Sans", "Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontFamily: '"Work Sans", sans-serif',
      fontWeight: 800,
      fontSize: '4rem',
      color: '#ffffff',
      letterSpacing: '-0.02em',
      textTransform: 'uppercase'
    },
    h2: {
      fontWeight: 600,
      color: '#2C5F2D',
    },
  },
});

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleFileAnalysis = async (file) => {
    setIsAnalyzing(true);
    try {
      // Step 1: Upload PDF to Azure Functions
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }
      
      const uploadResult = await uploadResponse.json();
      const fileId = uploadResult.file_id;
      
      // Step 2: Analyze the uploaded PDF
      const analysisResponse = await fetch(`/api/analyze/${fileId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!analysisResponse.ok) {
        throw new Error(`Analysis failed: ${analysisResponse.statusText}`);
      }
      
      const analysisResult = await analysisResponse.json();
      
      setAnalysisResult({
        summary: analysisResult.summary,
        keyPoints: analysisResult.key_points || [],
        confidence: analysisResult.confidence || 0.8
      });
      
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisResult({
        summary: `Analyse feilet: ${error.message}. Prøv igjen senere.`,
        keyPoints: ["Kontroller internettforbindelse", "Prøv med en mindre PDF-fil"],
        confidence: 0
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ minHeight: '100vh', bgcolor: '#13264A' }}>
        {/* Hero Section */}
        <Box
          sx={{
            bgcolor: '#13264A',
            py: 8,
            borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
            textAlign: 'center'
          }}
        >
          <Container maxWidth="lg">
            {/* DN Brand Text */}
            <Box sx={{ mb: 4 }}>
              <Typography 
                variant="h1" 
                component="h1"
                sx={{ 
                  fontFamily: '"Work Sans", sans-serif',
                  fontWeight: 800,
                  fontSize: { xs: '2.5rem', md: '4.2rem' },
                  color: '#ffffff',
                  letterSpacing: '-0.02em',
                  textTransform: 'uppercase',
                  mb: 2,
                  textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                  lineHeight: 1.1
                }}
              >
                Dagens Næringsliv
              </Typography>
            </Box>
            
            <Typography 
              variant="h2" 
              component="h2" 
              sx={{ 
                mb: 2,
                color: '#ffffff',
                fontWeight: 500,
                fontSize: { xs: '1.5rem', md: '2rem' }
              }}
            >
              AI Dokumentanalyse
            </Typography>
            
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                maxWidth: '600px',
                mx: 'auto',
                fontSize: '1.1rem',
                fontWeight: 400
              }}
            >
              Last opp dokumenter for å få en intelligent oppsummering og analyse
            </Typography>
          </Container>
        </Box>

        {/* Main Content */}
        <Container maxWidth="md" sx={{ py: 6 }}>
          {!analysisResult && !isAnalyzing && (
            <DocumentUpload onFileSelect={handleFileAnalysis} />
          )}

          {isAnalyzing && (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Description sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" sx={{ mb: 2 }}>
                Analyserer dokument...
              </Typography>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Dette kan ta noen minutter avhengig av dokumentets størrelse
              </Typography>
            </Paper>
          )}

          {analysisResult && (
            <ResultsDisplay 
              result={analysisResult} 
              onNewAnalysis={() => setAnalysisResult(null)}
            />
          )}
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;