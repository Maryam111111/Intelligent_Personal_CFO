"""Encryption utilities for sensitive data storage.

Provides encryption/decryption for:
- Stored financial data
- Cached API responses
- Temporary processing files
"""

import os
from cryptography.fernet import Fernet
from typing import Union
import json


class DataEncryption:
    """Handles encryption and decryption of sensitive files."""

    def __init__(self, key: str = None):
        """Initialize encryption with a key.
        
        Args:
            key: Base64-encoded encryption key. If None, reads from ENCRYPTION_KEY env var.
                 Generate with: python -c "from cryptography.fernet import Fernet; 
                                print(Fernet.generate_key().decode())"
        
        Raises:
            ValueError: If no key provided and ENCRYPTION_KEY not set
        """
        if key is None:
            key = os.environ.get('ENCRYPTION_KEY')
        
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY not set. Generate with: "
                "python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            )
        
        try:
            self.cipher = Fernet(key.encode())
        except Exception as e:
            raise ValueError(
                f"Invalid ENCRYPTION_KEY format: {str(e)}. "
                "Must be base64-encoded Fernet key."
            )

    def encrypt_file(self, file_path: str) -> str:
        """Encrypt a file in place.
        
        Args:
            file_path: Path to file to encrypt
            
        Returns:
            Path to encrypted file (original renamed to .encrypted)
        """
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.cipher.encrypt(data)
        
        encrypted_path = f"{file_path}.encrypted"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Securely delete original
        os.remove(file_path)
        
        return encrypted_path

    def decrypt_file(self, encrypted_path: str, output_path: str = None) -> str:
        """Decrypt a file.
        
        Args:
            encrypted_path: Path to .encrypted file
            output_path: Where to write decrypted file. If None, removes .encrypted ext
            
        Returns:
            Path to decrypted file
        """
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        if output_path is None:
            output_path = encrypted_path.replace('.encrypted', '')
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return output_path

    def encrypt_json(self, data: dict) -> str:
        """Encrypt JSON data to encrypted string.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        json_str = json.dumps(data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()

    def decrypt_json(self, encrypted_str: str) -> dict:
        """Decrypt JSON from encrypted string.
        
        Args:
            encrypted_str: Base64-encoded encrypted string
            
        Returns:
            Decrypted dictionary
        """
        decrypted = self.cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())
