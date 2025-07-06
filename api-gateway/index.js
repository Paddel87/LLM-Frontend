// Environment Variables laden
require('dotenv').config();

const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { logger, requestLogger, errorLogger } = require('./logger');

const app = express();

// Middleware Setup
app.use(cors({
  origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true
}));

// Rate Limiting
const limiter = rateLimit({
  windowMs: (process.env.RATE_LIMIT_WINDOW || 60) * 1000, // 1 minute default
  max: process.env.RATE_LIMIT_REQUESTS || 100, // 100 requests per window
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false
});

app.use(limiter);

// Request Logging Middleware
app.use(requestLogger);

// Health Check Endpoint
app.get('/health', (req, res) => {
  logger.info('Health check requested');
  res.json({ status: 'healthy', service: 'api-gateway', timestamp: new Date().toISOString() });
});

// API Info Endpoint
app.get('/api', (req, res) => {
  logger.info('API info requested');
  res.json({
    name: 'LLM Frontend API Gateway',
    version: '0.1.0',
    services: ['auth', 'core', 'payment', 'llm', 'rag'],
    timestamp: new Date().toISOString()
  });
});

// Proxy Middleware mit erweiterten Optionen
const createServiceProxy = (target, pathRewrite = {}) => {
  return createProxyMiddleware({
    target,
    changeOrigin: true,
    pathRewrite,
    onProxyReq: (proxyReq, req, res) => {
      // Request-ID an nachgelagerte Services weiterleiten
      proxyReq.setHeader('X-Request-ID', req.requestId);
      logger.debug('Proxying request', {
        requestId: req.requestId,
        method: req.method,
        originalUrl: req.url,
        target: target
      });
    },
    onProxyRes: (proxyRes, req, res) => {
      logger.debug('Received proxy response', {
        requestId: req.requestId,
        statusCode: proxyRes.statusCode,
        target: target
      });
    },
    onError: (err, req, res) => {
      logger.error('Proxy error', {
        requestId: req.requestId,
        error: err.message,
        target: target
      });
      res.status(502).json({
        error: 'Bad Gateway',
        message: 'Service temporarily unavailable'
      });
    }
  });
};

// Service Proxies
app.use('/api/auth', createServiceProxy('http://auth-service:8080'));
app.use('/api/core', createServiceProxy('http://backend-core:8080'));
app.use('/api/payment', createServiceProxy('http://payment-service:8080'));
app.use('/api/llm', createServiceProxy('http://llm-proxy:8080'));
app.use('/api/rag', createServiceProxy('http://rag-service:8080'));

// Error Logger Middleware
app.use(errorLogger);

// 404 Handler
app.use('*', (req, res) => {
  logger.warn('Route not found', {
    requestId: req.requestId,
    method: req.method,
    url: req.url
  });
  res.status(404).json({
    error: 'Not Found',
    message: 'The requested resource was not found'
  });
});

// Global Error Handler
app.use((error, req, res, next) => {
  logger.error('Unhandled error', {
    requestId: req.requestId,
    error: error.message,
    stack: error.stack
  });
  
  res.status(500).json({
    error: 'Internal Server Error',
    message: 'Something went wrong on our end'
  });
});

// Server starten
const PORT = process.env.API_PORT || 8080;
const HOST = process.env.API_HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
  logger.info('API Gateway started successfully', {
    port: PORT,
    host: HOST,
    environment: process.env.ENVIRONMENT || 'development',
    logLevel: process.env.LOG_LEVEL || 'info'
  });
});

// Graceful Shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Unhandled Promise Rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', {
    reason: reason,
    promise: promise
  });
});

// Uncaught Exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', {
    error: error.message,
    stack: error.stack
  });
  process.exit(1);
});