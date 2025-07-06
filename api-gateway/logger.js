/**
 * Winston-basierte Logging-Konfiguration für API-Gateway
 */
const winston = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');
const path = require('path');

// Log-Level von Environment Variable oder Default
const logLevel = process.env.LOG_LEVEL || 'info';
const logFormat = process.env.LOG_FORMAT || 'json';
const environment = process.env.ENVIRONMENT || 'development';

// Custom Format für Development
const devFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(({ level, message, timestamp, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
    return `${timestamp} [${level}] ${message} ${metaStr}`;
  })
);

// Custom Format für Production (JSON)
const prodFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf((info) => {
    return JSON.stringify({
      timestamp: info.timestamp,
      service: 'api-gateway',
      environment: environment,
      level: info.level,
      message: info.message,
      ...info
    });
  })
);

// Transports konfigurieren
const transports = [
  // Console Transport
  new winston.transports.Console({
    format: logFormat === 'json' ? prodFormat : devFormat,
    level: logLevel
  })
];

// File Transport falls LOG_FILE gesetzt ist
if (process.env.LOG_FILE) {
  transports.push(
    new DailyRotateFile({
      filename: process.env.LOG_FILE.replace('.log', '-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '14d',
      format: prodFormat,
      level: logLevel
    })
  );
}

// Error Log File
if (process.env.LOG_FILE) {
  transports.push(
    new DailyRotateFile({
      filename: process.env.LOG_FILE.replace('.log', '-error-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '30d',
      format: prodFormat,
      level: 'error'
    })
  );
}

// Logger erstellen
const logger = winston.createLogger({
  level: logLevel,
  format: logFormat === 'json' ? prodFormat : devFormat,
  transports: transports,
  exitOnError: false,
  // Unhandled exceptions und rejections loggen
  exceptionHandlers: [
    new winston.transports.Console({ format: devFormat }),
    ...(process.env.LOG_FILE ? [new winston.transports.File({ filename: 'exceptions.log' })] : [])
  ],
  rejectionHandlers: [
    new winston.transports.Console({ format: devFormat }),
    ...(process.env.LOG_FILE ? [new winston.transports.File({ filename: 'rejections.log' })] : [])
  ]
});

// Request Logger Middleware
const requestLogger = (req, res, next) => {
  const startTime = Date.now();
  
  // Request-ID generieren
  const requestId = require('crypto').randomUUID();
  req.requestId = requestId;
  
  // Log Request
  logger.info('HTTP Request', {
    requestId,
    method: req.method,
    url: req.url,
    userAgent: req.get('user-agent'),
    ip: req.ip,
    headers: req.headers
  });

  // Response abfangen für Logging
  const originalSend = res.send;
  res.send = function(data) {
    const duration = Date.now() - startTime;
    
    logger.info('HTTP Response', {
      requestId,
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      contentLength: res.get('content-length') || data?.length || 0
    });
    
    return originalSend.call(this, data);
  };

  next();
};

// Error Logger Middleware
const errorLogger = (error, req, res, next) => {
  logger.error('HTTP Error', {
    requestId: req.requestId,
    method: req.method,
    url: req.url,
    error: error.message,
    stack: error.stack,
    statusCode: res.statusCode
  });
  
  next(error);
};

module.exports = {
  logger,
  requestLogger,
  errorLogger
}; 