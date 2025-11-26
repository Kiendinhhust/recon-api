"""
Database models for the recon API
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Index
from sqlalchemy.orm import relationship

from app.deps import Base


class ScanStatus(str, Enum):
    """Scan status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SubdomainStatus(str, Enum):
    """Subdomain status enumeration"""
    FOUND = "found"
    LIVE = "live"
    DEAD = "dead"


class ScanJob(Base):
    """Scan job model"""
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    task_id = Column(String, nullable=True, index=True)  # Celery task ID for progress tracking
    domain = Column(String, nullable=False)
    status = Column(String, default=ScanStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    subdomains = relationship("Subdomain", back_populates="scan_job", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="scan_job", cascade="all, delete-orphan")
    waf_detections = relationship("WafDetection", back_populates="scan_job", cascade="all, delete-orphan")
    leak_detections = relationship("LeakDetection", back_populates="scan_job", cascade="all, delete-orphan")


class Subdomain(Base):
    """Subdomain model - optimized for httpx data"""
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False, index=True)

    # Core subdomain info
    subdomain = Column(String(255), nullable=False, index=True)
    url = Column(Text, nullable=True)  # Full URL with protocol (from httpx) - TEXT to handle long OAuth URLs

    # Live status (from httpx)
    status = Column(String, default=SubdomainStatus.FOUND)  # Keep for backward compatibility
    is_live = Column(Boolean, default=False, index=True)
    http_status = Column(Integer, nullable=True, index=True)

    # Httpx data - Essential fields
    title = Column(String(1024), nullable=True)  # Page title - increased to 1024 for long titles
    content_length = Column(Integer, nullable=True)  # Response size in bytes
    webserver = Column(String(128), nullable=True)  # e.g., "cloudflare", "nginx"
    final_url = Column(Text, nullable=True)  # URL after redirects - TEXT to handle long OAuth/SSO URLs

    # Httpx data - Useful fields
    response_time = Column(String(32), nullable=True)  # e.g., "11.4100539s" (keep as string from httpx)
    cdn_name = Column(String(128), nullable=True)  # e.g., "cloudflare"
    content_type = Column(String(128), nullable=True)  # e.g., "text/html"
    host = Column(String(64), nullable=True)  # Primary IP address

    # Httpx data - Arrays (stored as JSON)
    chain_status_codes = Column(JSON, nullable=True)  # e.g., [301, 200]
    ipv4_addresses = Column(JSON, nullable=True)  # e.g., ["104.20.28.61", "172.66.170.120"]
    ipv6_addresses = Column(JSON, nullable=True)  # e.g., ["2606:4700:10::ac42:aa78"]

    # Metadata
    discovered_by = Column(String(64), nullable=True)  # subfinder/amass/assetfinder
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="subdomains")
    screenshots = relationship("Screenshot", back_populates="subdomain", cascade="all, delete-orphan")
    technologies = relationship("Technology", back_populates="subdomain", cascade="all, delete-orphan")


class Screenshot(Base):
    """Screenshot model"""
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=True)
    url = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="screenshots")
    subdomain = relationship("Subdomain", back_populates="screenshots")


class WafDetection(Base):
    """WAF detection results from wafw00f"""
    __tablename__ = "waf_detections"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    url = Column(String, nullable=False)
    has_waf = Column(Boolean, default=False)
    waf_name = Column(String, nullable=True)
    waf_manufacturer = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="waf_detections")


class LeakDetection(Base):
    """Source code leak detection results from SourceLeakHacker"""
    __tablename__ = "leak_detections"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    base_url = Column(String, nullable=False)
    leaked_file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    http_status = Column(Integer, nullable=True)  # HTTP status code (200, 403, 404, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="leak_detections")


class Technology(Base):
    """Technology detected on subdomain (from httpx tech-detect)"""
    __tablename__ = "technologies"

    id = Column(Integer, primary_key=True, index=True)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)  # e.g., "WordPress", "Bootstrap:4"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subdomain = relationship("Subdomain", back_populates="technologies")

    # Unique constraint: one technology per subdomain
    __table_args__ = (
        Index('idx_tech_subdomain', 'subdomain_id', 'name', unique=True),
    )
