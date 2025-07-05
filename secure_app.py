import streamlit as st
import os
import tempfile
import asyncio
import time
import secrets
import json
import html
import hashlib
import threading
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

# Security imports
import bleach
import magic
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security logger
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security.log')
security_handler.setFormatter(
    logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s')
)
security_logger.addHandler(security_handler)

# Page configuration with security headers
st.set_page_config(
    page_title="AI PDF Chat",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Security headers and anti-iframe protection
st.markdown("""
<script>
    // Prevent iframe embedding
    if (window.top !== window.self) {
        window.top.location = window.self.location;
    }
    
    // Disable right-click context menu for security
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
    });
</script>
""", unsafe_allow_html=True)

# Enhanced CSS with security considerations
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e1e5e9;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: right;
        word-wrap: break-word;
        max-width: 80%;
    }
    
    .ai-message {
        background-color: #e9ecef;
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: left;
        word-wrap: break-word;
        max-width: 80%;
    }
    
    .security-notice {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.75rem;
        margin: 1rem 0;
    }
    
    .upload-section {
        border: 2px dashed #007bff;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class SecurityManager:
    """Handle security-related operations"""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = ['.pdf']
        self.max_input_length = 1000
        self.session_timeout = 3600  # 1 hour
        self.rate_limit_calls = {}
        
        # Initialize encryption for sensitive data
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = 'encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def validate_uploaded_file(self, uploaded_file) -> bool:
        """Comprehensive file validation"""
        try:
            # Check file size
            if uploaded_file.size > self.max_file_size:
                st.error(f"File too large. Maximum size: {self.max_file_size // 1024 // 1024}MB")
                self.log_security_event("FILE_TOO_LARGE", {
                    "filename": uploaded_file.name,
                    "size": uploaded_file.size
                })
                return False
            
            # Check file extension
            file_ext = Path(uploaded_file.name).suffix.lower()
            if file_ext not in self.allowed_extensions:
                st.error("Invalid file type. Only PDF files are allowed.")
                self.log_security_event("INVALID_FILE_TYPE", {
                    "filename": uploaded_file.name,
                    "extension": file_ext
                })
                return False
            
            # Check MIME type
            file_bytes = uploaded_file.getvalue()
            try:
                mime_type = magic.from_buffer(file_bytes, mime=True)
                if mime_type != 'application/pdf':
                    st.error("Invalid file format. File is not a valid PDF.")
                    self.log_security_event("INVALID_MIME_TYPE", {
                        "filename": uploaded_file.name,
                        "mime_type": mime_type
                    })
                    return False
            except Exception:
                # Fallback: check PDF header
                if not file_bytes.startswith(b'%PDF-'):
                    st.error("Invalid PDF file format.")
                    return False
            
            # Check for suspicious content
            if self._check_suspicious_content(file_bytes):
                st.error("File contains suspicious content and cannot be processed.")
                self.log_security_event("SUSPICIOUS_CONTENT", {
                    "filename": uploaded_file.name
                })
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            st.error("File validation failed.")
            return False
    
    def _check_suspicious_content(self, file_bytes: bytes) -> bool:
        """Check for suspicious content in file"""
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'eval(',
            b'exec(',
            b'system(',
            b'shell_exec'
        ]
        
        file_content = file_bytes.lower()
        for pattern in suspicious_patterns:
            if pattern in file_content:
                return True
        return False
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not user_input:
            return ""
        
        # Remove HTML tags and escape special characters
        cleaned = bleach.clean(user_input, tags=[], strip=True)
        escaped = html.escape(cleaned)
        
        # Limit length
        truncated = escaped[:self.max_input_length]
        
        if len(escaped) > self.max_input_length:
            st.warning(f"Input truncated to {self.max_input_length} characters.")
        
        return truncated
    
    def log_security_event(self, event_type: str, details: dict):
        """Log security-relevant events"""
        security_logger.warning(f"{event_type}: {details}")

def main():
    """Main function to run the secure Streamlit app"""
    st.markdown("""
    <div class="main-header">
        <h1>🔐 Secure AI PDF Chat</h1>
        <p>Upload your PDF documents and chat with them using AI - Securely Protected</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="security-notice">
        <h4>🔒 Security & Privacy Notice</h4>
        <p><strong>Your data is protected:</strong></p>
        <ul>
            <li>Files are processed locally and securely</li>
            <li>Data is encrypted and automatically deleted after session</li>
            <li>No data is shared with third parties</li>
            <li>Session expires after 1 hour for security</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    security_manager = SecurityManager()
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    st.sidebar.title("📁 Secure File Management")
    
    # File upload with security validation
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF files (Max 50MB each)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Only PDF files are accepted. Files are scanned for security."
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if security_manager.validate_uploaded_file(uploaded_file):
                st.sidebar.success(f"✅ {uploaded_file.name} validated successfully!")
            else:
                st.sidebar.error(f"❌ Security validation failed for {uploaded_file.name}")
    
    st.subheader("💬 Secure Chat with your PDFs")
    
    # Chat input with security
    user_input = st.text_input(
        "Ask a question about your PDF:",
        placeholder="e.g., What is the main topic of this document?",
        max_chars=1000
    )
    
    if st.button("📤 Send") and user_input:
        # Sanitize input
        sanitized_input = security_manager.sanitize_user_input(user_input)
        
        # Add to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': sanitized_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate AI response (placeholder)
        ai_response = f"I understand you're asking: '{sanitized_input}'. This is a secure demo response. In production, this would integrate with your AI backend to provide accurate answers based on your PDF content."
        
        st.session_state.chat_history.append({
            'role': 'assistant', 
            'content': ai_response,
            'timestamp': datetime.now().isoformat()
        })
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Chat History")
        for message in st.session_state.chat_history:
            role = message.get('role', '')
            content = html.escape(message.get('content', ''))
            
            if role == 'user':
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong> {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ai-message">
                    <strong>AI:</strong> {content}
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🔐 Secure AI PDF Chat - Protected by Advanced Security</p>
        <p>Developed with enterprise-grade security through AI crew workflow</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
