"""
Database models for the recon API
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
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
    """Subdomain model"""
    __tablename__ = "subdomains"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    subdomain = Column(String, nullable=False)
    status = Column(String, default=SubdomainStatus.FOUND)
    is_live = Column(Boolean, default=False)
    http_status = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # in milliseconds
    discovered_by = Column(String, nullable=True)  # tool that found it
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_job = relationship("ScanJob", back_populates="subdomains")
    screenshots = relationship("Screenshot", back_populates="subdomain", cascade="all, delete-orphan")


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
