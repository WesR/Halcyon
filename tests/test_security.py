import pytest
import halcyon
from halcyon.security import configure_security, get_security_mode, get_custom_security_settings
from halcyon.message import MessageContent, Message


class TestSecurityConfiguration:
    """Test security configuration system"""
    
    def setup_method(self):
        """Reset to default security mode before each test"""
        configure_security('strict')
    
    def test_default_strict_mode(self):
        """Test default strict security mode"""
        client = halcyon.Client()
        assert get_security_mode() == 'strict'
    
    def test_client_level_security_modes(self):
        """Test client-level security mode configuration"""
        # Test strict mode
        client_strict = halcyon.Client(security_mode='strict')
        assert get_security_mode() == 'strict'
        
        # Test lax mode
        client_lax = halcyon.Client(security_mode='lax')
        assert get_security_mode() == 'lax'
    
    def test_module_level_security_configuration(self):
        """Test module-level security configuration"""
        # Test strict mode
        configure_security('strict')
        assert get_security_mode() == 'strict'
        
        # Test lax mode
        configure_security('lax')
        assert get_security_mode() == 'lax'
        
        # Test custom mode
        configure_security('custom', extra='forbid', arbitrary_types=False)
        assert get_security_mode() == 'custom'
        settings = get_custom_security_settings()
        assert settings['extra'] == 'forbid'
        assert settings['arbitrary_types_allowed'] == False
    
    def test_invalid_security_mode(self):
        """Test invalid security mode raises error"""
        with pytest.raises(ValueError):
            configure_security('invalid_mode')
    
    def test_strict_mode_security(self):
        """Test strict mode drops unknown fields"""
        configure_security('strict')
        
        content = MessageContent({
            'msgtype': 'm.text',
            'body': 'Hello',
            'malicious_field': 'should_be_ignored',
            'another_unknown': 'also_ignored'
        })
        
        assert content.body == 'Hello'
        assert not hasattr(content, 'malicious_field')
        assert not hasattr(content, 'another_unknown')
        assert 'malicious_field' not in content.__dict__
        assert 'another_unknown' not in content.__dict__
    
    def test_lax_mode_security(self):
        """Test lax mode stores unknown fields"""
        configure_security('lax')
        
        content = MessageContent({
            'msgtype': 'm.text',
            'body': 'Hello',
            'extra_field': 'stored_value',
            'custom_data': {'nested': 'object'}
        })
        
        assert content.body == 'Hello'
        assert content.extra_field == 'stored_value'
        assert content.custom_data == {'nested': 'object'}
    
    def test_custom_mode_security(self):
        """Test custom security mode"""
        configure_security('custom', extra='forbid', arbitrary_types=False)
        
        assert get_security_mode() == 'custom'
        settings = get_custom_security_settings()
        assert settings['extra'] == 'forbid'
        assert settings['arbitrary_types_allowed'] == False
    
    def test_security_mode_inheritance(self):
        """Test that message components inherit security settings"""
        configure_security('lax')
        
        # Test that nested objects also respect lax mode
        message_data = {
            "type": "m.room.message",
            "sender": "@user:matrix.org",
            "content": {
                "msgtype": "m.text",
                "body": "Hello",
                "custom_field": "should_be_stored"
            },
            "origin_server_ts": 1632894724739,
            "event_id": "$test:matrix.org"
        }
        
        msg = Message(message_data)
        assert msg.content.custom_field == "should_be_stored"
    
    def test_security_mode_per_model_type(self):
        """Test security behavior for different model types"""
        configure_security('lax')
        
        # Test MessageContent
        content = MessageContent({
            'msgtype': 'm.text',
            'body': 'Test',
            'extra': 'value'
        })
        assert content.extra == 'value'
        
        # Test Message with room object (arbitrary_types should be allowed)
        from halcyon.room import room
        test_room = room(roomID="!test:matrix.org")
        
        msg = Message({
            "type": "m.room.message",
            "sender": "@user:matrix.org",
            "content": {"msgtype": "m.text", "body": "Test"},
            "origin_server_ts": 1632894724739,
            "event_id": "$test:matrix.org"
        }, room=test_room)
        
        assert msg.room is not None
        assert msg.room.id == "!test:matrix.org"
    
    def test_thread_safety(self):
        """Test that security configuration is thread-safe"""
        import threading
        import time
        
        results = []
        
        def worker(mode, delay):
            time.sleep(delay)
            configure_security(mode)
            results.append(get_security_mode())
        
        threads = [
            threading.Thread(target=worker, args=('strict', 0.01)),
            threading.Thread(target=worker, args=('lax', 0.02)),
            threading.Thread(target=worker, args=('strict', 0.03)),
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Last setting should win
        assert get_security_mode() == 'strict'
        assert len(results) == 3
    
    def test_backward_compatibility(self):
        """Test that existing code still works with security system"""
        # Test that old-style instantiation still works
        configure_security('strict')
        
        # These should all work without security mode parameters
        content = MessageContent({'msgtype': 'm.text', 'body': 'Hello'})
        msg = Message({
            "type": "m.room.message",
            "sender": "@user:matrix.org",
            "content": {"msgtype": "m.text", "body": "Test"},
            "origin_server_ts": 1632894724739,
            "event_id": "$test:matrix.org"
        })
        
        assert content.body == 'Hello'
        assert msg.content.body == 'Test'
    
    def test_security_with_different_data_types(self):
        """Test security with various data types in lax mode"""
        configure_security('lax')
        
        content = MessageContent({
            'msgtype': 'm.text',
            'body': 'Hello',
            'number_field': 42,
            'boolean_field': True,
            'list_field': [1, 2, 3],
            'dict_field': {'nested': 'data'},
            'none_field': None
        })
        
        assert content.number_field == 42
        assert content.boolean_field is True
        assert content.list_field == [1, 2, 3]
        assert content.dict_field == {'nested': 'data'}
        assert content.none_field is None


class TestSecurityModeTransitions:
    """Test transitions between security modes"""
    
    def test_mode_transitions(self):
        """Test switching between security modes"""
        # Start strict
        configure_security('strict')
        content1 = MessageContent({'msgtype': 'm.text', 'body': 'Hello', 'extra': 'ignored'})
        assert not hasattr(content1, 'extra')
        
        # Switch to lax
        configure_security('lax')
        content2 = MessageContent({'msgtype': 'm.text', 'body': 'Hello', 'extra': 'stored'})
        assert content2.extra == 'stored'
        
        # Switch to custom
        configure_security('custom', extra='ignore', arbitrary_types=False)
        assert get_security_mode() == 'custom'
        
        # Back to strict
        configure_security('strict')
        content3 = MessageContent({'msgtype': 'm.text', 'body': 'Hello', 'extra': 'ignored_again'})
        assert not hasattr(content3, 'extra')
    
    def test_client_overrides_global_config(self):
        """Test that client configuration overrides global settings"""
        # Set global config
        configure_security('strict')
        assert get_security_mode() == 'strict'
        
        # Client overrides it
        client = halcyon.Client(security_mode='lax')
        assert get_security_mode() == 'lax'
        
        # Verify lax mode is active
        content = MessageContent({'msgtype': 'm.text', 'body': 'Hello', 'extra': 'stored'})
        assert content.extra == 'stored'