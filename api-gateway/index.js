/**
 * Enhanced API Gateway für LLM-Frontend
 * Zentrale Schnittstelle für alle Microservices
 */

require('express-async-errors');
require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');
const swaggerUi = require('swagger-ui-express');
const { v4: uuidv4 } = require('uuid');
const { logger, requestLogger, errorLogger } = require('./logger');
const openApiSpec = require('./openapi');

const app = express();

// ===================================================
// KONFIGURATION
// ===================================================

const PORT = process.env.API_PORT || 8080;
const HOST = process.env.API_HOST || '0.0.0.0';
const ENVIRONMENT = process.env.ENVIRONMENT || 'development';
const API_VERSION = 'v1';

// Service URLs
const SERVICES = {
  AUTH: process.env.AUTH_SERVICE_URL || 'http://auth-service:8080',
  CORE: process.env.CORE_SERVICE_URL || 'http://backend-core:8080',
  PAYMENT: process.env.PAYMENT_SERVICE_URL || 'http://payment-service:8080',
  LLM: process.env.LLM_SERVICE_URL || 'http://llm-proxy:8080',
  RAG: process.env.RAG_SERVICE_URL || 'http://rag-service:8080'
};

// Startup-Zeit für Uptime-Berechnung
const startupTime = Date.now();

// ===================================================
// SECURITY MIDDLEWARE
// ===================================================

// Helmet für Security Headers
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  crossOriginEmbedderPolicy: false
}));

// ===================================================
// GENERAL MIDDLEWARE
// ===================================================

// Compression
app.use(compression());

// JSON Parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request ID Middleware
app.use((req, res, next) => {
  req.id = req.headers['x-request-id'] || uuidv4();
  res.setHeader('X-Request-ID', req.id);
  next();
});

// CORS Middleware
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = (process.env.CORS_ORIGINS || 'http://localhost:3000').split(',');
    
    // In Development alle Origins erlauben wenn keine Origin gesendet wird (z.B. mobile apps)
    if (!origin && ENVIRONMENT === 'development') {
      return callback(null, true);
    }
    
    if (allowedOrigins.includes(origin) || allowedOrigins.includes('*')) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID', 'X-API-Key'],
  exposedHeaders: ['X-Request-ID', 'X-RateLimit-Limit', 'X-RateLimit-Remaining']
};

app.use(cors(corsOptions));

// Request Logging
app.use(requestLogger);

// ===================================================
// RATE LIMITING
// ===================================================

// Allgemeines Rate Limiting
const generalLimiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW || '60') * 1000, // 1 Minute
  max: parseInt(process.env.RATE_LIMIT_REQUESTS || '100'), // 100 Requests
  message: {
    error: 'Too many requests',
    detail: 'Please try again later',
    code: 'RATE_LIMIT_EXCEEDED'
  },
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => {
    // Health checks von Rate Limiting ausschließen
    return req.path === '/health' || req.path === '/';
  }
});

// Auth-spezifisches Rate Limiting (strenger)
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 Minuten
  max: 5, // 5 Login-Versuche pro 15 Minuten
  message: {
    error: 'Too many authentication attempts',
    detail: 'Please try again later',
    code: 'AUTH_RATE_LIMIT_EXCEEDED'
  },
  standardHeaders: true,
  legacyHeaders: false
});

app.use(generalLimiter);

// ===================================================
// OPENAPI DOCUMENTATION
// ===================================================

// Swagger UI
app.use('/docs', swaggerUi.serve, swaggerUi.setup(openApiSpec, {
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: 'LLM-Frontend API Docs',
  swaggerOptions: {
    persistAuthorization: true,
    displayRequestDuration: true,
    filter: true,
    showExtensions: true,
    showCommonExtensions: true
  }
}));

// OpenAPI JSON Endpoint
app.get('/openapi.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(openApiSpec);
});

// ===================================================
// HEALTH CHECK ENDPOINTS
// ===================================================

/**
 * @swagger
 * /:
 *   get:
 *     summary: Root endpoint
 *     tags: [System]
 *     responses:
 *       200:
 *         description: API Gateway information
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/MessageResponse'
 */
app.get('/', (req, res) => {
  logger.info('Root endpoint accessed', { requestId: req.id });
  res.json({
    name: 'LLM-Frontend API Gateway',
    version: '1.0.0',
    environment: ENVIRONMENT,
    api_version: API_VERSION,
    documentation: '/docs',
    health: '/health',
    timestamp: new Date().toISOString(),
    request_id: req.id
  });
});

/**
 * @swagger
 * /health:
 *   get:
 *     summary: Comprehensive health check
 *     tags: [System]
 *     responses:
 *       200:
 *         description: System health status
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/HealthResponse'
 */
app.get('/health', async (req, res) => {
  logger.debug('Health check accessed', { requestId: req.id });
  
  const uptime = (Date.now() - startupTime) / 1000;
  const services = {};
  
  // Service Health Checks (parallel)
  const healthChecks = Object.entries(SERVICES).map(async ([name, url]) => {
    const startTime = Date.now();
    try {
      const response = await fetch(`${url}/health`, {
        method: 'GET',
        timeout: 5000,
        headers: { 'X-Request-ID': req.id }
      });
      
      const responseTime = Date.now() - startTime;
      
      services[name.toLowerCase()] = {
        status: response.ok ? 'healthy' : 'unhealthy',
        response_time: responseTime,
        url: url
      };
    } catch (error) {
      services[name.toLowerCase()] = {
        status: 'unhealthy',
        response_time: Date.now() - startTime,
        error: error.message,
        url: url
      };
    }
  });
  
  await Promise.all(healthChecks);
  
  // Overall Status bestimmen
  const allHealthy = Object.values(services).every(service => service.status === 'healthy');
  const overallStatus = allHealthy ? 'healthy' : 'degraded';
  
  const healthData = {
    status: overallStatus,
    service: 'api-gateway',
    timestamp: new Date().toISOString(),
    uptime: uptime,
    environment: ENVIRONMENT,
    version: '1.0.0',
    services: services,
    request_id: req.id
  };
  
  // Log health check
  logger.info('Health check completed', {
    requestId: req.id,
    status: overallStatus,
    uptime: uptime,
    serviceCount: Object.keys(services).length
  });
  
  res.status(overallStatus === 'healthy' ? 200 : 503).json(healthData);
});

// ===================================================
// SERVICE PROXY MIDDLEWARE
// ===================================================

function createServiceProxy(serviceName, target, pathRewrite = {}) {
  return createProxyMiddleware({
    target,
    changeOrigin: true,
    pathRewrite,
    timeout: 30000,
    proxyTimeout: 30000,
    
    onProxyReq: (proxyReq, req, res) => {
      // Request-ID weiterleiten
      proxyReq.setHeader('X-Request-ID', req.id);
      proxyReq.setHeader('X-Forwarded-For', req.ip);
      proxyReq.setHeader('X-Gateway-Service', serviceName);
      
      logger.debug('Proxying request', {
        requestId: req.id,
        service: serviceName,
        method: req.method,
        originalUrl: req.originalUrl,
        target: target,
        userAgent: req.get('User-Agent')
      });
    },
    
    onProxyRes: (proxyRes, req, res) => {
      // Response Headers setzen
      proxyRes.headers['X-Request-ID'] = req.id;
      proxyRes.headers['X-Service'] = serviceName;
      
      logger.debug('Received proxy response', {
        requestId: req.id,
        service: serviceName,
        statusCode: proxyRes.statusCode,
        responseTime: Date.now() - req.startTime
      });
    },
    
    onError: (err, req, res) => {
      logger.error('Proxy error', {
        requestId: req.id,
        service: serviceName,
        error: err.message,
        stack: err.stack,
        target: target
      });
      
      // Strukturierte Fehlerantwort
      if (!res.headersSent) {
        res.status(502).json({
          error: 'Service temporarily unavailable',
          detail: `${serviceName} service is not responding`,
          code: 'SERVICE_UNAVAILABLE',
          service: serviceName,
          timestamp: new Date().toISOString(),
          request_id: req.id
        });
      }
    }
  });
}

// ===================================================
// API VERSIONING & ROUTING
// ===================================================

// API v1 Routes mit Service-spezifischen Rate Limitern
app.use(`/api/${API_VERSION}/auth/login`, authLimiter);
app.use(`/api/${API_VERSION}/auth/register`, authLimiter);

// Service Proxies mit versionierten Routen
app.use(`/api/${API_VERSION}/auth`, createServiceProxy('auth', SERVICES.AUTH));
app.use(`/api/${API_VERSION}/core`, createServiceProxy('core', SERVICES.CORE));
app.use(`/api/${API_VERSION}/payment`, createServiceProxy('payment', SERVICES.PAYMENT));
app.use(`/api/${API_VERSION}/llm`, createServiceProxy('llm', SERVICES.LLM));
app.use(`/api/${API_VERSION}/rag`, createServiceProxy('rag', SERVICES.RAG));

// Legacy Routes (ohne Versionierung) für Rückwärtskompatibilität
app.use('/api/auth', createServiceProxy('auth', SERVICES.AUTH));
app.use('/api/core', createServiceProxy('core', SERVICES.CORE));
app.use('/api/payment', createServiceProxy('payment', SERVICES.PAYMENT));
app.use('/api/llm', createServiceProxy('llm', SERVICES.LLM));
app.use('/api/rag', createServiceProxy('rag', SERVICES.RAG));

// ===================================================
// ERROR HANDLING
// ===================================================

// 404 Handler
app.use('*', (req, res) => {
  logger.warn('Route not found', {
    requestId: req.id,
    method: req.method,
    url: req.originalUrl,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  
  res.status(404).json({
    error: 'Not Found',
    detail: `The requested resource '${req.originalUrl}' was not found`,
    code: 'RESOURCE_NOT_FOUND',
    timestamp: new Date().toISOString(),
    request_id: req.id,
    available_endpoints: {
      documentation: '/docs',
      health: '/health',
      api: `/api/${API_VERSION}`
    }
  });
});

// Global Error Handler
app.use((error, req, res, next) => {
  const errorId = uuidv4();
  
  logger.error('Unhandled application error', {
    requestId: req.id,
    errorId: errorId,
    error: error.message,
    stack: error.stack,
    method: req.method,
    url: req.originalUrl,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  
  // CORS Error handling
  if (error.message === 'Not allowed by CORS') {
    return res.status(403).json({
      error: 'CORS Error',
      detail: 'Origin not allowed by CORS policy',
      code: 'CORS_NOT_ALLOWED',
      timestamp: new Date().toISOString(),
      request_id: req.id,
      error_id: errorId
    });
  }
  
  // Syntax Error (z.B. malformed JSON)
  if (error instanceof SyntaxError && error.status === 400 && 'body' in error) {
    return res.status(400).json({
      error: 'Invalid JSON',
      detail: 'Request body contains invalid JSON',
      code: 'INVALID_JSON',
      timestamp: new Date().toISOString(),
      request_id: req.id,
      error_id: errorId
    });
  }
  
  // Payload too large
  if (error.code === 'LIMIT_FILE_SIZE' || error.code === 'LIMIT_FIELD_SIZE') {
    return res.status(413).json({
      error: 'Payload too large',
      detail: 'Request payload exceeds size limit',
      code: 'PAYLOAD_TOO_LARGE',
      timestamp: new Date().toISOString(),
      request_id: req.id,
      error_id: errorId
    });
  }
  
  // Generic Internal Server Error
  const statusCode = error.status || error.statusCode || 500;
  
  res.status(statusCode).json({
    error: 'Internal Server Error',
    detail: ENVIRONMENT === 'development' ? error.message : 'Something went wrong on our end',
    code: 'INTERNAL_SERVER_ERROR',
    timestamp: new Date().toISOString(),
    request_id: req.id,
    error_id: errorId,
    ...(ENVIRONMENT === 'development' && { stack: error.stack })
  });
});

// ===================================================
// GRACEFUL SHUTDOWN
// ===================================================

process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception', { error: error.message, stack: error.stack });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection', { reason: reason, promise: promise });
});

// ===================================================
// SERVER START
// ===================================================

const server = app.listen(PORT, HOST, () => {
  logger.info('API Gateway started successfully', {
    port: PORT,
    host: HOST,
    environment: ENVIRONMENT,
    apiVersion: API_VERSION,
    services: Object.keys(SERVICES).length,
    documentation: `http://${HOST}:${PORT}/docs`,
    nodeVersion: process.version,
    pid: process.pid
  });
  
  // Service-URLs loggen
  Object.entries(SERVICES).forEach(([name, url]) => {
    logger.info('Service configured', { service: name, url: url });
  });
});

// Handle server errors
server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    logger.error(`Port ${PORT} is already in use`);
  } else {
    logger.error('Server error', { error: error.message });
  }
  process.exit(1);
});

module.exports = app;