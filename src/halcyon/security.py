"""
Security configuration for Pydantic model validation:
- 'strict': Secure defaults (extra='ignore', arbitrary_types=False) 
- 'lax': Backward compatible (extra='allow', arbitrary_types=True)
- 'custom': User-defined settings
"""

import threading
from typing import Literal, Optional, Dict, Any
from pydantic import ConfigDict


SecurityMode = Literal['strict', 'lax', 'custom']


class SecurityConfig:
    """Thread-safe security configuration manager"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._mode: SecurityMode = 'strict'  # Default to secure mode
        self._custom_settings: Dict[str, Any] = {}
    
    def set_mode(self, mode: SecurityMode) -> None:
        """Set the security mode for all models"""
        with self._lock:
            if mode not in ('strict', 'lax', 'custom'):
                raise ValueError(f"Invalid security mode: {mode}. Must be 'strict', 'lax', or 'custom'")
            self._mode = mode
    
    def set_custom(self, extra: Literal['allow', 'ignore', 'forbid'] = 'ignore',
                   arbitrary_types: bool = False, **kwargs) -> None:
        """Set custom security settings"""
        with self._lock:
            self._mode = 'custom'
            self._custom_settings = {
                'extra': extra,
                'arbitrary_types_allowed': arbitrary_types,
                **kwargs
            }
    
    def get_config_dict(self, **overrides) -> ConfigDict:
        """Get Pydantic ConfigDict for current security mode"""
        with self._lock:
            if self._mode == 'strict':
                config = {
                    'extra': 'ignore',
                    'arbitrary_types_allowed': False,
                }
            elif self._mode == 'lax':
                config = {
                    'extra': 'allow', 
                    'arbitrary_types_allowed': True,
                }
            elif self._mode == 'custom':
                config = self._custom_settings.copy()
            else:
                # Fallback to strict
                config = {
                    'extra': 'ignore',
                    'arbitrary_types_allowed': False,
                }
            
            # Apply any overrides
            config.update(overrides)
            
            return ConfigDict(**config)
    
    def get_mode(self) -> SecurityMode:
        """Get current security mode"""
        with self._lock:
            return self._mode
    
    def get_custom_settings(self) -> Dict[str, Any]:
        """Get current custom settings"""
        with self._lock:
            return self._custom_settings.copy()


# Global security configuration instance
_security_config = SecurityConfig()


def configure_security(mode: SecurityMode = 'strict', **kwargs) -> None:
    """
    Configure security mode for all Halcyon models.
    
    Args:
        mode: Security mode ('strict', 'lax', or 'custom')
        **kwargs: Custom settings when mode='custom' (extra, arbitrary_types, etc.)
    
    Examples:
        # Use strict mode (default)
        configure_security('strict')
        
        # Use lax mode for backward compatibility
        configure_security('lax')
        
        # Use custom settings
        configure_security('custom', extra='forbid', arbitrary_types=False)
    """
    if mode == 'custom':
        _security_config.set_custom(**kwargs)
    else:
        _security_config.set_mode(mode)


def get_security_config() -> ConfigDict:
    """Get current security configuration as Pydantic ConfigDict"""
    return _security_config.get_config_dict()


def get_security_mode() -> SecurityMode:
    """Get current security mode"""
    return _security_config.get_mode()


def get_custom_security_settings() -> Dict[str, Any]:
    """Get current custom security settings"""
    return _security_config.get_custom_settings()


# Convenience functions for specific model needs
def get_message_config(**overrides) -> ConfigDict:
    """Get config for Message models (may need arbitrary_types for room objects)"""
    # Message class needs arbitrary_types for room object compatibility
    if get_security_mode() != 'lax':
        overrides.setdefault('arbitrary_types_allowed', True)
    return _security_config.get_config_dict(**overrides)


def get_nested_config(**overrides) -> ConfigDict:
    """Get config for nested models (MessageContent, FileInfo, etc.)"""
    return _security_config.get_config_dict(**overrides)