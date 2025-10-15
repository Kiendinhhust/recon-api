"""
Parsers for tool outputs
"""
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SubdomainResult:
    """Standardized subdomain result"""
    subdomain: str
    source: str
    confidence: float = 1.0


@dataclass
class LiveCheckResult:
    """Result from live check (httpx)"""
    url: str
    status_code: Optional[int] = None
    response_time: Optional[int] = None
    title: Optional[str] = None
    tech: List[str] = None
    is_live: bool = False


class SubfinderParser:
    """Parser for subfinder output"""
    
    @staticmethod
    def parse(output: str) -> List[SubdomainResult]:
        """Parse subfinder output"""
        results = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('[') and '.' in line:
                # Clean up the subdomain
                subdomain = line.lower().strip()
                if subdomain:
                    results.append(SubdomainResult(
                        subdomain=subdomain,
                        source="subfinder"
                    ))
        
        return results


class AmassParser:
    """Parser for amass output - handles both simple and graph format"""

    @staticmethod
    def parse(output: str) -> List[SubdomainResult]:
        """Parse amass output and extract only FQDNs (subdomains)"""
        results = []
        seen_domains = set()
        lines = output.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is graph format (contains arrows -->)
            if '-->' in line:
                # Extract FQDN from graph format
                # Format: "subdomain.example.com (FQDN) --> relationship --> target"
                fqdn = AmassParser._extract_fqdn_from_graph(line)
                if fqdn and fqdn not in seen_domains:
                    seen_domains.add(fqdn)
                    results.append(SubdomainResult(
                        subdomain=fqdn,
                        source="amass"
                    ))
            else:
                # Simple format - just domain names
                if not line.startswith('[') and '.' in line:
                    parts = line.split()
                    if parts:
                        subdomain = parts[0].lower().strip()
                        if subdomain and '.' in subdomain and subdomain not in seen_domains:
                            seen_domains.add(subdomain)
                            results.append(SubdomainResult(
                                subdomain=subdomain,
                                source="amass"
                            ))

        return results

    @staticmethod
    def _extract_fqdn_from_graph(line: str) -> Optional[str]:
        """Extract FQDN from amass graph format line"""
        import re

        # Pattern to match: "domain.com (FQDN)" at the start of line
        # Example: "bot.fpt.ai (FQDN) --> a_record --> 124.197.26.207"
        match = re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\s+\(FQDN\)', line)

        if match:
            # Extract just the domain part (before the space and (FQDN))
            domain = line.split('(FQDN)')[0].strip()
            return domain.lower()

        return None


class AssetfinderParser:
    """Parser for assetfinder output"""
    
    @staticmethod
    def parse(output: str) -> List[SubdomainResult]:
        """Parse assetfinder output"""
        results = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and '.' in line:
                subdomain = line.lower().strip()
                if subdomain:
                    results.append(SubdomainResult(
                        subdomain=subdomain,
                        source="assetfinder"
                    ))
        
        return results


class HttpxParser:
    """Parser for httpx output"""
    
    @staticmethod
    def parse(output: str) -> List[LiveCheckResult]:
        """Parse httpx JSON output"""
        results = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Try to parse as JSON first (httpx -json output)
                data = json.loads(line)
                result = HttpxParser._parse_json_line(data)
                if result:
                    results.append(result)
            except json.JSONDecodeError:
                # Fallback to simple URL parsing
                if line.startswith('http'):
                    results.append(LiveCheckResult(
                        url=line,
                        is_live=True
                    ))
        
        return results
    
    @staticmethod
    def _parse_json_line(data: Dict[str, Any]) -> Optional[LiveCheckResult]:
        """Parse a single JSON line from httpx"""
        if 'url' not in data:
            return None
            
        return LiveCheckResult(
            url=data.get('url', ''),
            status_code=data.get('status_code'),
            response_time=data.get('response_time'),
            title=data.get('title', '').strip() if data.get('title') else None,
            tech=data.get('tech', []) if data.get('tech') else [],
            is_live=True
        )


class GoWitnessParser:
    """Parser for gowitness output"""
    
    @staticmethod
    def parse_db_output(db_path: str) -> List[Dict[str, Any]]:
        """Parse gowitness SQLite database output"""
        import sqlite3
        
        results = []
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query the URLs table
            cursor.execute("""
                SELECT url, final_url, response_code, response_reason, 
                       title, filename, created_at
                FROM urls
            """)
            
            for row in cursor.fetchall():
                results.append({
                    'url': row[0],
                    'final_url': row[1],
                    'status_code': row[2],
                    'status_reason': row[3],
                    'title': row[4],
                    'filename': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
        except Exception as e:
            print(f"Error parsing gowitness database: {e}")
        
        return results
    
    @staticmethod
    def parse_file_list(output: str) -> List[str]:
        """Parse list of generated screenshot files"""
        files = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.endswith('.png') or line.endswith('.jpg'):
                files.append(line)
        
        return files


class OutputCombiner:
    """Combine and deduplicate results from multiple tools"""
    
    @staticmethod
    def combine_subdomains(results_list: List[List[SubdomainResult]]) -> List[SubdomainResult]:
        """Combine subdomain results from multiple tools"""
        seen = set()
        combined = []
        
        for results in results_list:
            for result in results:
                if result.subdomain not in seen:
                    seen.add(result.subdomain)
                    combined.append(result)
        
        return sorted(combined, key=lambda x: x.subdomain)
    
    @staticmethod
    def merge_live_results(subdomains: List[str], live_results: List[LiveCheckResult]) -> Dict[str, LiveCheckResult]:
        """Merge live check results with subdomain list"""
        live_map = {}
        
        # Create a mapping of domain to live result
        for result in live_results:
            # Extract domain from URL
            domain = result.url.replace('http://', '').replace('https://', '').split('/')[0]
            live_map[domain] = result
        
        return live_map
