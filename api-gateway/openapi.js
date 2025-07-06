/**
 * OpenAPI 3.0 Spezifikation für LLM-Frontend API Gateway
 */
const swaggerJsdoc = require('swagger-jsdoc');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'LLM-Frontend API Gateway',
      version: '1.0.0',
      description: `
        **Zentrale API für das LLM-Frontend System**
        
        Dieses API Gateway orchestriert alle Microservices und bietet eine einheitliche Schnittstelle für:
        
        - 🔐 Authentication & Authorization
        - 📊 Backend Core Services
        - 💳 Payment Processing
        - 🤖 LLM Proxy Services
        - 🔍 RAG & Vector Search
        
        ## Features
        
        - JWT-basierte Authentifizierung
        - Rate Limiting
        - Request/Response Logging
        - CORS Support
        - API Versioning
        - Comprehensive Error Handling
        
        ## Getting Started
        
        1. Registriere einen Account über \`/api/v1/auth/register\`
        2. Authentifiziere dich über \`/api/v1/auth/login\`
        3. Verwende den erhaltenen JWT Token für authentifizierte Endpoints
        
        ## Authentication
        
        Für authentifizierte Endpoints verwende den Authorization Header:
        \`\`\`
        Authorization: Bearer <your-jwt-token>
        \`\`\`
      `,
      contact: {
        name: 'LLM-Frontend Team',
        email: 'support@llm-frontend.example',
        url: 'https://github.com/Paddel87/LLM-Frontend'
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT'
      }
    },
    servers: [
      {
        url: 'http://localhost:8080',
        description: 'Development Server'
      },
      {
        url: 'https://api.llm-frontend.example',
        description: 'Production Server'
      }
    ],
    components: {
      securitySchemes: {
        BearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
      },
      schemas: {
        // Allgemeine Schemas
        HealthResponse: {
          type: 'object',
          properties: {
            status: {
              type: 'string',
              enum: ['healthy', 'degraded', 'unhealthy'],
              description: 'Overall system health status'
            },
            service: {
              type: 'string',
              description: 'Service name'
            },
            timestamp: {
              type: 'string',
              format: 'date-time',
              description: 'Health check timestamp'
            },
            database: {
              type: 'boolean',
              description: 'Database connectivity status'
            },
            uptime: {
              type: 'number',
              description: 'Service uptime in seconds'
            },
            services: {
              type: 'object',
              description: 'Individual service health status',
              additionalProperties: {
                type: 'object',
                properties: {
                  status: { type: 'string' },
                  response_time: { type: 'number' }
                }
              }
            }
          }
        },
        ErrorResponse: {
          type: 'object',
          properties: {
            error: {
              type: 'string',
              description: 'Error message'
            },
            detail: {
              type: 'string',
              description: 'Detailed error description'
            },
            code: {
              type: 'string',
              description: 'Error code'
            },
            timestamp: {
              type: 'string',
              format: 'date-time'
            },
            path: {
              type: 'string',
              description: 'Request path that caused the error'
            }
          }
        },
        MessageResponse: {
          type: 'object',
          properties: {
            message: {
              type: 'string',
              description: 'Response message'
            },
            detail: {
              type: 'string',
              description: 'Additional details'
            }
          }
        },
        
        // Authentication Schemas
        UserRegistration: {
          type: 'object',
          required: ['email', 'username', 'password'],
          properties: {
            email: {
              type: 'string',
              format: 'email',
              description: 'User email address'
            },
            username: {
              type: 'string',
              minLength: 3,
              pattern: '^[a-zA-Z0-9]+$',
              description: 'Alphanumeric username (min 3 characters)'
            },
            password: {
              type: 'string',
              minLength: 8,
              description: 'Password (min 8 characters, must contain uppercase, lowercase, and digit)'
            },
            full_name: {
              type: 'string',
              description: 'User full name (optional)'
            }
          }
        },
        UserLogin: {
          type: 'object',
          required: ['email', 'password'],
          properties: {
            email: {
              type: 'string',
              format: 'email'
            },
            password: {
              type: 'string'
            }
          }
        },
        TokenResponse: {
          type: 'object',
          properties: {
            access_token: {
              type: 'string',
              description: 'JWT access token'
            },
            refresh_token: {
              type: 'string',
              description: 'JWT refresh token'
            },
            token_type: {
              type: 'string',
              default: 'bearer'
            },
            expires_in: {
              type: 'integer',
              description: 'Token expiration time in seconds'
            }
          }
        },
        UserResponse: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            email: { type: 'string', format: 'email' },
            username: { type: 'string' },
            full_name: { type: 'string' },
            is_active: { type: 'boolean' },
            is_admin: { type: 'boolean' },
            email_verified: { type: 'boolean' },
            created_at: { type: 'string', format: 'date-time' },
            last_login: { type: 'string', format: 'date-time' }
          }
        },
        
        // Project & Chat Schemas
        Project: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            name: { type: 'string' },
            description: { type: 'string' },
            owner_id: { type: 'integer' },
            is_shared: { type: 'boolean' },
            color: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
            created_at: { type: 'string', format: 'date-time' },
            updated_at: { type: 'string', format: 'date-time' }
          }
        },
        Chat: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            title: { type: 'string' },
            project_id: { type: 'integer' },
            folder_id: { type: 'integer' },
            model_name: { type: 'string' },
            system_prompt: { type: 'string' },
            model_config: { type: 'object' },
            temperature: { type: 'number', minimum: 0, maximum: 2 },
            max_tokens: { type: 'integer', minimum: 1 },
            is_archived: { type: 'boolean' },
            created_at: { type: 'string', format: 'date-time' },
            updated_at: { type: 'string', format: 'date-time' }
          }
        },
        Message: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            chat_id: { type: 'integer' },
            role: { type: 'string', enum: ['user', 'assistant', 'system'] },
            content: { type: 'string' },
            token_count: { type: 'integer' },
            cost: { type: 'number' },
            metadata: { type: 'object' },
            created_at: { type: 'string', format: 'date-time' }
          }
        },
        
        // LLM Schemas
        LLMRequest: {
          type: 'object',
          required: ['model', 'messages'],
          properties: {
            model: {
              type: 'string',
              description: 'LLM model name',
              enum: ['gpt-4', 'gpt-3.5-turbo', 'claude-3', 'gemini-pro']
            },
            messages: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  role: { type: 'string', enum: ['user', 'assistant', 'system'] },
                  content: { type: 'string' }
                }
              }
            },
            temperature: { type: 'number', minimum: 0, maximum: 2, default: 0.7 },
            max_tokens: { type: 'integer', minimum: 1, default: 4000 },
            stream: { type: 'boolean', default: false }
          }
        },
        LLMResponse: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            model: { type: 'string' },
            choices: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  message: {
                    type: 'object',
                    properties: {
                      role: { type: 'string' },
                      content: { type: 'string' }
                    }
                  },
                  finish_reason: { type: 'string' }
                }
              }
            },
            usage: {
              type: 'object',
              properties: {
                prompt_tokens: { type: 'integer' },
                completion_tokens: { type: 'integer' },
                total_tokens: { type: 'integer' },
                cost: { type: 'number' }
              }
            }
          }
        },
        
        // Payment Schemas
        PaymentRequest: {
          type: 'object',
          required: ['amount'],
          properties: {
            amount: { type: 'number', minimum: 1 },
            currency: { type: 'string', default: 'USD' },
            payment_method: { type: 'string' }
          }
        },
        PaymentResponse: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            stripe_payment_id: { type: 'string' },
            amount: { type: 'number' },
            currency: { type: 'string' },
            status: { type: 'string', enum: ['pending', 'completed', 'failed', 'refunded'] },
            created_at: { type: 'string', format: 'date-time' }
          }
        }
      },
      responses: {
        UnauthorizedError: {
          description: 'Unauthorized - Invalid or missing authentication token',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' }
            }
          }
        },
        ForbiddenError: {
          description: 'Forbidden - Insufficient permissions',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' }
            }
          }
        },
        NotFoundError: {
          description: 'Resource not found',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' }
            }
          }
        },
        ValidationError: {
          description: 'Validation error - Invalid input data',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' }
            }
          }
        },
        InternalServerError: {
          description: 'Internal server error',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' }
            }
          }
        },
        RateLimitError: {
          description: 'Rate limit exceeded',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' }
            }
          }
        }
      }
    },
    tags: [
      {
        name: 'System',
        description: 'System health and information endpoints'
      },
      {
        name: 'Authentication',
        description: 'User authentication and authorization'
      },
      {
        name: 'Users',
        description: 'User management operations'
      },
      {
        name: 'Projects',
        description: 'Project and folder management'
      },
      {
        name: 'Chats',
        description: 'Chat and message management'
      },
      {
        name: 'LLM',
        description: 'Large Language Model interactions'
      },
      {
        name: 'RAG',
        description: 'Retrieval Augmented Generation'
      },
      {
        name: 'Payments',
        description: 'Payment and billing operations'
      }
    ]
  },
  apis: ['./routes/*.js', './index.js'] // Pfade zu den API-Definitionen
};

const specs = swaggerJsdoc(options);

module.exports = specs; 