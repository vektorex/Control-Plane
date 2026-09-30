"""
Pydantic argument schemas for GitHub connector operations.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GetRepositoryArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(..., description="Repository owner (user or organization)")
    repo: str = Field(..., description="Repository name")


class ListRepositoriesArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    visibility: Optional[str] = Field(default="all", description="Visibility: all | public | private")
    sort: Optional[str] = Field(default="updated", description="Sort field: created | updated | pushed | full_name")
    limit: int = Field(default=30, ge=1, le=100, description="Max repositories to return")


class SearchRepositoriesArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str = Field(..., min_length=1, description="GitHub search query, e.g. 'language:python topic:fastapi'")
    sort: Optional[str] = Field(default=None, description="Sort field: stars | forks | help-wanted-issues | updated")
    order: Optional[str] = Field(default="desc", description="Sort direction: asc | desc")
    limit: int = Field(default=30, ge=1, le=100, description="Max repositories to return")


class GetIssueArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., ge=1, description="Issue number")


class ListIssuesArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    state: str = Field(default="open", description="Issue state: open | closed | all")
    limit: int = Field(default=30, ge=1, le=100, description="Max issues to return")


class SearchIssuesArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str = Field(..., min_length=1, description="GitHub issue search query, e.g. 'repo:owner/repo is:issue is:open bug'")
    sort: Optional[str] = Field(default=None, description="Sort field: comments | reactions | created | updated")
    order: Optional[str] = Field(default="desc", description="Sort direction: asc | desc")
    limit: int = Field(default=30, ge=1, le=100, description="Max issues to return")


class GetPullRequestArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., ge=1, description="Pull request number")


class ListPullRequestsArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    state: str = Field(default="open", description="PR state: open | closed | all")
    limit: int = Field(default=30, ge=1, le=100, description="Max pull requests to return")


class GetFileContentsArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path within the repository, e.g. 'src/main.py'")
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit SHA (default: default branch)")


class SearchCodeArgs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str = Field(..., min_length=1, description="Code search query, e.g. 'auth_required repo:owner/repo'")
    sort: Optional[str] = Field(default=None, description="Sort field: indexed")
    order: Optional[str] = Field(default="desc", description="Sort direction: asc | desc")
    limit: int = Field(default=30, ge=1, le=100, description="Max code results to return")
