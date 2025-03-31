# IndustrialDoc - Smart Machine Documentation System

A powerful, secure file management system designed for industrial documentation, created by Team Motion Minds.

## Team Members
- Prince Patel(Team Leader)
- Dhruv Patel
- Ruhan Kureshi
- Tabrez Qureshi

## Overview
IndustrialDoc is a web-based application that provides a secure and organized environment for managing industrial machine documentation. The system allows for efficient storage, retrieval, and sharing of technical documentation with features specifically designed for industrial environments.

## Features

### Core File Management
- **File Upload/Download**: Support for various file types (PDF, DOC, DOCX, TXT, ZIP, RAR, PPTX, images)
- **Organized Folder Structure**: Create and navigate through a hierarchical folder system
- **Bulk Operations**: Delete multiple files simultaneously
- **File Renaming**: Easily rename files and folders
-  **File Type Filtering**: Filter files By their Type

### Security Features
- **Password Protection**: Secure access to administrative functions
- **Master Password System**: Additional security layer for critical changes
- **File Password Protection**: Option to encrypt downloads with password protection
- **Change Password Functionality**: Ability to update admin password with master password verification

### Search and Accessibility
- **Search Functionality**: Quickly find files and folders with search feature
- **File Filtering**: Filter files by type (PDF, DOC, ZIP, images, etc.)
- **QR Code Generation**: Create QR codes for quick access to specific folders
- **Mobile-Friendly Design**: Responsive interface for all device sizes

### Error Handling
- **Size Limitations**: 50MB maximum file size with appropriate error messages
- **Comprehensive Error Handling**: User-friendly error messages for all operations
- **Duplicate File Management**: Prevents accidental overwrites with automatic rename

## Technical Requirements
- Python 3.x
- Flask 3.0.0
- Werkzeug 3.0.1
- qrcode 7.4.2
- PIL (Python Imaging Library)
- cryptography.fernet

## Installation

1. Clone the repository:
```
git clone https://github.com/MotionMinds/IndustrialDoc.git
cd IndustrialDoc
```

2. Install required packages:
```
pip install -r requirements.txt
```

3. Run the application:
```
python app.py
```

4. Access the application in your browser:
```
http://localhost:5000
```

## Usage Guide

### Basic Navigation
- The home page provides an overview of the system features
- Use the file browser to navigate through folders
- Upload files into specific folders (files cannot be uploaded to root directory)
- Create new folders in the root directory

### Administrative Functions
- Default admin password: "123456" (should be changed immediately in production)
- Default master password: "master123" (should be changed in the code for production)
- Default file password: "file@123" (for encrypted downloads)

### Security Considerations
- Change the default passwords before deploying in production
- Regularly back up your data
- Consider implementing HTTPS in production environments

## Project Structure
- `/uploads`: Directory for all uploaded files and folders
- `/templates`: HTML templates for the web interface
- `/static`: CSS, JavaScript, and other static assets
- `app.py`: Main application file with all routes and functionality
- `requirements.txt`: List of Python dependencies



## Contact
For any inquiries or support, please contact any of the team members. 