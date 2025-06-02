from pathlib import Path
from typing import Any, Dict
from jinja2 import Template, Environment, StrictUndefined, FileSystemLoader, FunctionLoader, TemplateError, meta
from supabase import create_client
from pydantic_settings import BaseSettings
from functools import lru_cache
import frontmatter
import os


class PromptSettings(BaseSettings):
    supabase_url: str | None = None
    supabase_key: str | None = None
    template_path: str = 'prompts/templates'

    class Config:
        env_file = ".prompting_env"


class PromptManager:
    _settings = PromptSettings()
    _supabase_client = None
    _jinja_environment = None

    if _settings.supabase_url and _settings.supabase_key:
        _supabase_client = create_client(_settings.supabase_url, _settings.supabase_key)

    if _supabase_client is None:
        template_dir = Path.cwd() / _settings.template_path
        _jinja_environment = Environment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined
        )
    else:
        _jinja_environment = Environment(
            loader=FunctionLoader(lambda name: PromptManager.load_supabase_template(name).source),
            undefined=StrictUndefined
        )

    @staticmethod
    def get_supabase_client():
        if PromptManager._supabase_client is None:
            raise RuntimeError("Supabase client is not configured. Please set supabase_url and supabase_key.")
        return PromptManager._supabase_client

    @staticmethod
    def load_template(template_name: str) -> Template:
        """Load a template from either supabase or a local file"""
        if PromptManager._supabase_client is not None:
            return PromptManager.load_supabase_template(template_name)
        return PromptManager.load_local_template(template_name)
    
    @staticmethod
    @lru_cache(maxsize=32)
    def load_local_template(path: str) -> Template:
        """Read a template file from the local file system."""
        env = PromptManager._jinja_environment
        template_path = f"{path}.j2"
        source, filename, _ = env.loader.get_source(env, template_path)
        template_data = frontmatter.loads(source)
        tmpl = env.from_string(template_data.content)
        tmpl.meta = template_data.metadata
        tmpl.source = property(lambda self: source)
        return tmpl

    @staticmethod
    @lru_cache(maxsize=32)
    def load_supabase_template(template_name: str) -> Template:
        """Fetch a template string from Supabase by name, with caching."""
        if PromptManager._supabase_client is None:
            raise RuntimeError("Supabase client is not configured. Cannot load template from Supabase.")
        response = PromptManager._supabase_client.table("prompts").select("content, description, author").eq("name", template_name).single().execute()
        if "data" in response and response.data:
            env = PromptManager._jinja_environment
            template_content = response.data["content"]
            tmpl = env.from_string(template_content)
            tmpl.meta = {
                "description": response.data.get("description", "No description provided"),
                "author": response.data.get("author", "Unknown"),
            }
            tmpl.source = property(lambda self: template_content)
            return tmpl
        raise ValueError(f"Template '{template_name}' not found in Supabase")

    @staticmethod
    def template_info(template: Template) -> Dict[str, Any]:
        env = PromptManager._jinja_environment
        parsed = env.parse(template.source)
        return {
            "name": template.name,
            "description": getattr(template, "meta", {}).get('description', 'No description provided'),
            "author": getattr(template, "meta", {}).get('author', 'Unknown'),
            "variables": meta.find_undeclared_variables(parsed),
        }

    @staticmethod
    def render_template(template: Template, context: dict) -> str:
        """Render a Jinja2 template with a given context."""
        return template.render(**context)
