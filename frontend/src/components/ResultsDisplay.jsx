import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  Card,
  CardContent
} from '@mui/material';
import {
  CheckCircle,
  Refresh,
  TrendingUp,
  Article,
  Insights
} from '@mui/icons-material';

const ResultsDisplay = ({ result, onNewAnalysis }) => {
  const { summary, keyPoints, confidence, full_analysis } = result;
  
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const getConfidenceText = (confidence) => {
    if (confidence >= 0.8) return 'Høy pålitelighet';
    if (confidence >= 0.6) return 'Middels pålitelighet';
    return 'Lav pålitelighet';
  };

  return (
    <Box sx={{ space: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: '#f3f7f3' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" sx={{ color: 'primary.main', display: 'flex', alignItems: 'center' }}>
            <Article sx={{ mr: 2, fontSize: 40 }} />
            Analyse ferdig
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip 
              label={getConfidenceText(confidence)}
              color={getConfidenceColor(confidence)}
              icon={<CheckCircle />}
            />
            <Chip 
              label={`${Math.round(confidence * 100)}%`}
              variant="outlined"
            />
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Dokumentet har blitt analysert med AI. Se resultatet nedenfor.
        </Typography>
      </Paper>

      {/* Summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
            <Insights sx={{ mr: 1 }} />
            Oppsummering
          </Typography>
          <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
            {summary}
          </Typography>
        </CardContent>
      </Card>

      {/* Key Points */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
            <TrendingUp sx={{ mr: 1 }} />
            Hovedpunkter
          </Typography>
          <List>
            {keyPoints.map((point, index) => (
              <ListItem key={index} sx={{ pl: 0 }}>
                <ListItemIcon>
                  <CheckCircle color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary={point}
                  primaryTypographyProps={{
                    fontSize: '1.1rem',
                    lineHeight: 1.6
                  }}
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      {/* Full Structured Analysis */}
      {full_analysis && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h5" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <Insights sx={{ mr: 1 }} />
              Detaljert analyse
            </Typography>
            <Box sx={{ 
              bgcolor: 'rgba(0,0,0,0.05)', 
              p: 2, 
              borderRadius: 1,
              maxHeight: 400,
              overflow: 'auto',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              fontSize: '0.9rem',
              lineHeight: 1.6
            }}>
              {full_analysis}
            </Box>
          </CardContent>
        </Card>
      )}

      <Divider sx={{ my: 3 }} />

      {/* Action Buttons */}
      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Refresh />}
          onClick={onNewAnalysis}
          sx={{ minWidth: 200 }}
        >
          Analyser nytt dokument
        </Button>
      </Box>

      {/* Footer */}
      <Typography 
        variant="caption" 
        sx={{ 
          display: 'block', 
          textAlign: 'center', 
          mt: 3, 
          color: 'text.secondary' 
        }}
      >
        Analyse utført av Azure AI Services • Dagens Næringsliv
      </Typography>
    </Box>
  );
};

export default ResultsDisplay;