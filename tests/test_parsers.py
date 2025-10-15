"""
Tests for parser modules
"""
import pytest
from app.services.parsers import (
    SubfinderParser, AmassParser, AssetfinderParser, 
    HttpxParser, OutputCombiner
)


class TestSubfinderParser:
    """Test subfinder output parser"""
    
    def test_parse_basic_output(self):
        output = """
        api.example.com
        www.example.com
        mail.example.com
        """
        results = SubfinderParser.parse(output)
        
        assert len(results) == 3
        assert results[0].subdomain == "api.example.com"
        assert results[0].source == "subfinder"
        assert results[1].subdomain == "www.example.com"
        assert results[2].subdomain == "mail.example.com"
    
    def test_parse_empty_output(self):
        output = ""
        results = SubfinderParser.parse(output)
        assert len(results) == 0
    
    def test_parse_with_noise(self):
        output = """
        [INFO] Starting subfinder
        api.example.com
        [DEBUG] Found subdomain
        www.example.com
        """
        results = SubfinderParser.parse(output)
        
        assert len(results) == 2
        assert results[0].subdomain == "api.example.com"
        assert results[1].subdomain == "www.example.com"


class TestAmassParser:
    """Test amass output parser"""
    
    def test_parse_basic_output(self):
        output = """
        api.example.com
        www.example.com 192.168.1.1
        mail.example.com [additional info]
        """
        results = AmassParser.parse(output)
        
        assert len(results) == 3
        assert results[0].subdomain == "api.example.com"
        assert results[1].subdomain == "www.example.com"
        assert results[2].subdomain == "mail.example.com"


class TestAssetfinderParser:
    """Test assetfinder output parser"""
    
    def test_parse_basic_output(self):
        output = """
        api.example.com
        www.example.com
        mail.example.com
        """
        results = AssetfinderParser.parse(output)
        
        assert len(results) == 3
        assert all(r.source == "assetfinder" for r in results)


class TestHttpxParser:
    """Test httpx output parser"""
    
    def test_parse_json_output(self):
        output = '''
        {"url":"https://api.example.com","status_code":200,"response_time":150,"title":"API"}
        {"url":"https://www.example.com","status_code":200,"response_time":200,"title":"Home"}
        '''
        results = HttpxParser.parse(output)
        
        assert len(results) == 2
        assert results[0].url == "https://api.example.com"
        assert results[0].status_code == 200
        assert results[0].response_time == 150
        assert results[0].title == "API"
        assert results[0].is_live == True
    
    def test_parse_simple_url_output(self):
        output = """
        https://api.example.com
        https://www.example.com
        """
        results = HttpxParser.parse(output)
        
        assert len(results) == 2
        assert results[0].url == "https://api.example.com"
        assert results[0].is_live == True
        assert results[1].url == "https://www.example.com"


class TestOutputCombiner:
    """Test output combination utilities"""
    
    def test_combine_subdomains(self):
        from app.services.parsers import SubdomainResult
        
        results1 = [
            SubdomainResult("api.example.com", "subfinder"),
            SubdomainResult("www.example.com", "subfinder")
        ]
        results2 = [
            SubdomainResult("api.example.com", "amass"),  # duplicate
            SubdomainResult("mail.example.com", "amass")
        ]
        
        combined = OutputCombiner.combine_subdomains([results1, results2])
        
        assert len(combined) == 3
        subdomains = [r.subdomain for r in combined]
        assert "api.example.com" in subdomains
        assert "www.example.com" in subdomains
        assert "mail.example.com" in subdomains
    
    def test_merge_live_results(self):
        from app.services.parsers import LiveCheckResult
        
        subdomains = ["api.example.com", "www.example.com", "dead.example.com"]
        live_results = [
            LiveCheckResult("https://api.example.com", status_code=200, is_live=True),
            LiveCheckResult("https://www.example.com", status_code=200, is_live=True)
        ]
        
        merged = OutputCombiner.merge_live_results(subdomains, live_results)
        
        assert "api.example.com" in merged
        assert "www.example.com" in merged
        assert "dead.example.com" not in merged
        assert merged["api.example.com"].status_code == 200
