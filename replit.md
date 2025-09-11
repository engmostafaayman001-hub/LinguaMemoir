# Overview

This is a professional Arabic/RTL Point of Sale (POS) system built with Flask. The application serves retail businesses by providing comprehensive inventory management, sales processing, employee management, and reporting capabilities. The system features a bilingual interface (Arabic/English) with RTL (right-to-left) layout support and includes modern POS features like barcode scanning, invoice generation, and role-based access control.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **Flask with SQLAlchemy**: Core web framework using Flask-SQLAlchemy for ORM and database operations
- **Database**: Configured for both SQLite (development) and PostgreSQL (production) with connection pooling
- **Authentication**: Flask-Login with role-based permissions (admin, manager, cashier)
- **Form Handling**: WTForms with CSRF protection and Arabic validation messages
- **Session Management**: Secure session handling with environment-based secret keys

## Frontend Architecture
- **Template Engine**: Jinja2 with Bootstrap 5 RTL for Arabic interface
- **CSS Framework**: Bootstrap 5 with RTL support and custom Arabic typography
- **JavaScript**: Vanilla JavaScript with modular structure (main.js, pos.js, barcode-scanner.js)
- **Responsive Design**: Mobile-first approach with Arabic font support and RTL layout
- **Real-time Features**: AJAX-based product search, barcode scanning, and dynamic cart management

## Database Schema
- **Employee Management**: User roles, permissions, and authentication
- **Product Catalog**: Bilingual product names, SKU, barcode, pricing, and inventory
- **Category System**: Hierarchical product categorization
- **Sales Tracking**: Invoice generation, sale items, and transaction history
- **Inventory Management**: Stock levels, movement tracking, and low-stock alerts

## File Structure
- **Static Assets**: Organized CSS, JavaScript, and uploaded images
- **Templates**: Base template with component inheritance for consistent UI
- **Business Logic**: Separated forms, models, routes, and utility functions
- **Media Handling**: Image upload, resizing, and PDF invoice generation

## Security Features
- **Role-Based Access Control**: Three-tier permission system
- **CSRF Protection**: Form validation with secure tokens
- **File Upload Security**: Secure filename handling and file type validation
- **Password Hashing**: Werkzeug security for password management
- **Session Security**: Environment-based session configuration

## Point of Sale Features
- **Barcode Integration**: HTML5-QRCode library for camera-based scanning
- **Real-time Cart**: Dynamic product addition, quantity management, and total calculations
- **Invoice Generation**: PDF creation with Arabic support using ReportLab
- **Payment Processing**: Cash transaction handling with change calculation
- **Receipt Printing**: Formatted invoice generation and storage

# External Dependencies

## Core Web Framework
- **Flask**: Main web framework with extensions for login, CSRF, and database ORM
- **SQLAlchemy**: Database ORM with PostgreSQL and SQLite support
- **WTForms**: Form validation with Arabic localization

## Frontend Libraries
- **Bootstrap 5**: RTL-enabled CSS framework for Arabic interface
- **Font Awesome**: Icon library for UI elements
- **HTML5-QRCode**: Camera-based barcode scanning functionality

## File Processing
- **Pillow (PIL)**: Image processing, resizing, and optimization
- **ReportLab**: PDF generation for invoices with Arabic text support
- **Werkzeug**: File upload security and password hashing utilities

## Production Considerations
- **ProxyFix**: WSGI middleware for proper header handling behind reverse proxies
- **Database Pooling**: Connection pool management for production scalability
- **File Storage**: Local file system for product images and generated invoices

## Development Tools
- **Environment Variables**: Configuration for database URLs, session secrets, and file paths
- **Logging**: Debug-level logging for development troubleshooting
- **Static File Handling**: Organized asset management for CSS, JavaScript, and uploads