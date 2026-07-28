from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
import uuid
from backend.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "User"
    id = Column(String, primary_key=True, default=generate_uuid)
    firstName = Column(String, nullable=True)
    lastName = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    profileImage = Column(String, nullable=True)
    passwordHash = Column(String, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    deletedAt = Column(DateTime(timezone=True), nullable=True)

    onboarding = relationship("Onboarding", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    passwordResets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    googleConnections = relationship("GoogleConnection", back_populates="user", cascade="all, delete-orphan")
    linkedinSearches = relationship("LinkedInSearch", back_populates="user", cascade="all, delete-orphan")
    masterProfile = relationship("MasterProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Onboarding(Base):
    __tablename__ = "Onboarding"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    currentStep = Column(Integer, default=1)
    completedSteps = Column(JSON, nullable=True)
    onboardingCompleted = Column(Boolean, default=False)
    resumeUploaded = Column(Boolean, default=False)
    resumeProcessed = Column(Boolean, default=False)
    googleConnected = Column(Boolean, default=False)

    user = relationship("User", back_populates="onboarding")


class UserPreference(Base):
    __tablename__ = "UserPreference"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    firstLoginCompleted = Column(Boolean, default=False)
    tourCompleted = Column(Boolean, default=False)
    theme = Column(String, default="dark")
    dashboardLayout = Column(JSON, nullable=True)
    lastDashboardVisit = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="preferences")


class Account(Base):
    __tablename__ = "Account"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    providerAccountId = Column(String, nullable=False)

    user = relationship("User", back_populates="accounts")


class Session(Base):
    __tablename__ = "Session"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    refreshToken = Column(String, unique=True, nullable=False)
    userAgent = Column(String, nullable=True)
    ipAddress = Column(String, nullable=True)
    expiresAt = Column(DateTime(timezone=True), nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")


class VerificationToken(Base):
    __tablename__ = "VerificationToken"
    identifier = Column(String, primary_key=True) # Composite key not strictly needed for this migration if we just use id
    token = Column(String, unique=True, nullable=False, primary_key=True)
    expiresAt = Column(DateTime(timezone=True), nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "PasswordResetToken"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expiresAt = Column(DateTime(timezone=True), nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="passwordResets")


class AuditLog(Base):
    __tablename__ = "AuditLog"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    ipAddress = Column(String, nullable=True)
    userAgent = Column(String, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())


class Resume(Base):
    __tablename__ = "Resume"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    fileUrl = Column(String, nullable=False)
    fileName = Column(String, nullable=False)
    
    # Metadata and Status
    status = Column(String, default="ACTIVE")
    checksum = Column(String, nullable=True)
    fileSize = Column(Integer, nullable=True)
    mimeType = Column(String, nullable=True)
    pageCount = Column(Integer, nullable=True)
    wordCount = Column(Integer, nullable=True)
    uploadSource = Column(String, nullable=True)
    processingStatus = Column(String, default="PENDING")
    parserVersion = Column(String, nullable=True)
    
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    jobs = relationship("ResumeProcessingJob", back_populates="resume", cascade="all, delete-orphan")


class ResumeVersion(Base):
    __tablename__ = "ResumeVersion"
    id = Column(String, primary_key=True, default=generate_uuid)
    resumeId = Column(String, ForeignKey("Resume.id", ondelete="CASCADE"), nullable=False)
    versionNumber = Column(Integer, nullable=False)
    parsedText = Column(Text, nullable=True)
    structuredData = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="versions")
    embeddings = relationship("ResumeEmbedding", back_populates="resumeVersion", cascade="all, delete-orphan")


class ResumeProcessingJob(Base):
    __tablename__ = "ResumeProcessingJob"
    id = Column(String, primary_key=True, default=generate_uuid)
    resumeId = Column(String, ForeignKey("Resume.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="PENDING")
    error = Column(Text, nullable=True)
    retryCount = Column(Integer, default=0)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    resume = relationship("Resume", back_populates="jobs")


class ResumeEmbedding(Base):
    __tablename__ = "ResumeEmbedding"
    id = Column(String, primary_key=True, default=generate_uuid)
    resumeVersionId = Column(String, ForeignKey("ResumeVersion.id", ondelete="CASCADE"), nullable=False)
    vectorData = Column(JSON, nullable=True)

    resumeVersion = relationship("ResumeVersion", back_populates="embeddings")


class GoogleConnection(Base):
    __tablename__ = "GoogleConnection"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    email = Column(String, nullable=False)
    accessToken = Column(Text, nullable=False)
    refreshToken = Column(Text, nullable=False)
    scopes = Column(Text, nullable=False)
    expiresAt = Column(DateTime(timezone=True), nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="googleConnections")

class LinkedInSearch(Base):
    __tablename__ = "LinkedInSearch"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    searchName = Column(String, nullable=True)
    role = Column(String, nullable=False)
    locations = Column(JSON, nullable=False)
    postedWithin = Column(String, nullable=False)
    maxJobs = Column(Integer, default=10)
    experienceMode = Column(String, nullable=False)
    searchStatus = Column(String, default="PENDING")

    jobsScraped = Column(Integer, default=0)
    jobsProcessed = Column(Integer, default=0)
    jobsTailored = Column(Integer, default=0)
    jobsSkipped = Column(Integer, default=0)
    jobsApplied = Column(Integer, default=0)

    startedAt = Column(DateTime(timezone=True), nullable=True)
    completedAt = Column(DateTime(timezone=True), nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="linkedinSearches")


class MasterProfile(Base):
    __tablename__ = "MasterProfile"
    id = Column(String, primary_key=True, default=generate_uuid)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    contactInfo = Column(JSON, nullable=True)
    targetTitles = Column(JSON, nullable=True)
    workExperience = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    education = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    achievements = Column(JSON, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="masterProfile")


class AgentRun(Base):
    """
    Structured event for LLM observability, tracking single LLM execution steps.
    """
    __tablename__ = "AgentRun"
    id = Column(String, primary_key=True, default=generate_uuid)
    runId = Column(String, nullable=False, index=True)
    traceId = Column(String, nullable=True, index=True)
    agentName = Column(String, nullable=False)
    model = Column(String, nullable=False)
    promptVersion = Column(String, nullable=True)
    temperature = Column(Integer, nullable=True) # Float typically but schema is flex
    
    # Payload
    input = Column(Text, nullable=True)
    retrievedContext = Column(Text, nullable=True)
    toolsUsed = Column(JSON, nullable=True)
    output = Column(Text, nullable=True)
    
    # Metrics
    confidence = Column(Integer, nullable=True) # Could be float
    latency = Column(Integer, nullable=True) # In milliseconds
    tokens = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True) # Float but integer is fine for microcents
    retryCount = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    
    # Quality metrics (populated asynchronously by LLM-as-a-judge)
    accuracy = Column(Integer, nullable=True)
    precision = Column(Integer, nullable=True)
    recall = Column(Integer, nullable=True)
    f1 = Column(Integer, nullable=True)
    hallucination = Column(Integer, nullable=True)
    groundedness = Column(Integer, nullable=True)
    helpfulness = Column(Integer, nullable=True)
    toxicity = Column(Integer, nullable=True)
    completeness = Column(Integer, nullable=True)
    consistency = Column(Integer, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    userId = Column(String, ForeignKey("User.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User")


class AgentMetric(Base):
    """
    Aggregate metrics over time.
    """
    __tablename__ = "AgentMetric"
    id = Column(String, primary_key=True, default=generate_uuid)
    agentName = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    successRate = Column(Integer, nullable=True)
    retryPercent = Column(Integer, nullable=True)
    averageCost = Column(Integer, nullable=True)
    averageTokens = Column(Integer, nullable=True)
    averageLatency = Column(Integer, nullable=True)
    humanOverridePercent = Column(Integer, nullable=True)
    escalationPercent = Column(Integer, nullable=True)
    failurePercent = Column(Integer, nullable=True)
    recoveryPercent = Column(Integer, nullable=True)
    toolErrorPercent = Column(Integer, nullable=True)
    reasoningSteps = Column(Integer, nullable=True)

