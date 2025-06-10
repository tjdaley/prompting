from pathlib import Path
from typing import Any, Dict, Union
from jinja2 import Template, Environment, StrictUndefined, FileSystemLoader, FunctionLoader, TemplateNotFound, TemplateError, meta
from supabase import create_client, Client
from pydantic_settings import BaseSettings
from functools import lru_cache
import frontmatter # type: ignore


class PromptSettings(BaseSettings):
    supabase_url: str | None = None
    supabase_key: str | None = None
    template_path: str = 'prompts/templates'
    use_cache: bool = True
    forced_source: str = ''
    

    class Config:
        env_file = ".prompting_env"


class PromptManager:
    _settings = PromptSettings()
    _supabase_client: Union[Client, None] = None
    _jinja_environment: Union[Environment, None] = None
    _use_cache = _settings.use_cache

    if _settings.supabase_url and _settings.supabase_key and _settings.forced_source <> 'local':
        _supabase_client = create_client(_settings.supabase_url, _settings.supabase_key) # type: ignore

    if _supabase_client is None:
        template_dir = Path.cwd() / _settings.template_path
        _jinja_environment = Environment( # type: ignore
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined
        )
    else:
        _jinja_environment = Environment( # type: ignore
            loader=FunctionLoader(lambda name: PromptManager.load_supabase_template(name).source), # type: ignore
            undefined=StrictUndefined
        )

    @staticmethod
    def get_supabase_client() -> Client: # type: ignore
        if PromptManager._supabase_client is None: # type: ignore
            raise RuntimeError("Supabase client is not configured. Please set supabase_url and supabase_key.")
        return PromptManager._supabase_client # type: ignore

    @staticmethod
    def load_template(template_name: str) -> Template:
        """Load a template from either supabase or a local file"""
        try:
            if PromptManager._supabase_client is not None: # type: ignore
                return PromptManager.load_supabase_template(template_name) # type: ignore
            return PromptManager.load_local_template(template_name) # type: ignore
        except TemplateNotFound:
            raise ValueError(f"Template '{template_name}' not found in the configured template paths.")
        except TemplateError as e:
            raise ValueError(f"Error loading template '{template_name}': {e}")
        except FileNotFoundError as e:
            raise ValueError(f"Template file '{template_name}' not found: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while loading template '{template_name}': {e}")
    
    @staticmethod
    @lru_cache(maxsize=32)
    def _cached_load_local_template(path: str) -> Template:
        """Read a template file from the local file system."""
        return PromptManager._load_local_template(path)

    @staticmethod
    def _load_local_template(path: str) -> Template:
        env = PromptManager._jinja_environment
        assert env is not None, "Jinja environment is not properly initialized."
        assert env.loader is not None, "Jinja environment loader is not set."
        template_path = f"{path}.j2"
        source, _, _ = env.loader.get_source(env, template_path)
        template_data = frontmatter.loads(source)
        tmpl = env.from_string(template_data.content)
        tmpl.meta = template_data.metadata # type: ignore
        setattr(tmpl, 'source', source)
        return tmpl
    
    @staticmethod
    def load_local_template(template_name: str) -> Template:
        """Load a template from the local file system."""
        if PromptManager._use_cache:
            return PromptManager._cached_load_local_template(template_name)
        return PromptManager._load_local_template(template_name)

    @staticmethod
    @lru_cache(maxsize=32)
    def _cached_load_supabase_template(template_name: str) -> Template:
        """Fetch a template string from Supabase by name, with caching."""
        return PromptManager._load_supabase_template(template_name)
    
    @staticmethod
    def _load_supabase_template(template_name: str) -> Template:
        """Fetch a template string from Supabase by name."""
        assert PromptManager._jinja_environment is not None, "Jinja environment is not properly initialized."
        if PromptManager._supabase_client is None:
            raise RuntimeError("Supabase client is not configured. Cannot load template from Supabase.")
        response = PromptManager._supabase_client.table("prompts").select("content, description, author").eq("name", template_name).single().execute()
        if "data" in response and response.data: # type: ignore
            env = PromptManager._jinja_environment
            template_content = response.data["content"]
            tmpl = env.from_string(template_content)
            tmpl.meta = { # type: ignore
                "description": response.data.get("description", "No description provided"),
                "author": response.data.get("author", "Unknown"),
            }
            setattr(tmpl, 'source', template_content)
            return tmpl
        raise ValueError(f"Template '{template_name}' not found in Supabase")
    
    @staticmethod
    def load_supabase_template(template_name: str) -> Template:
        """Load a template from Supabase."""
        if PromptManager._use_cache:
            return PromptManager._cached_load_supabase_template(template_name)
        return PromptManager._load_supabase_template(template_name)

    @staticmethod
    def template_info(template: Template) -> Dict[str, Any]:
        env = PromptManager._jinja_environment
        assert env is not None, "Jinja environment is not properly initialized."
        parsed = env.parse(template.source) # type: ignore
        return {
            "name": template.name,
            "description": getattr(template, "meta", {}).get('description', 'No description provided'),
            "author": getattr(template, "meta", {}).get('author', 'Unknown'),
            "variables": meta.find_undeclared_variables(parsed),
        }

    @staticmethod
    def render(template: Template, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template with a given context."""
        return template.render(**context)

    @staticmethod
    def clear_cache():
        PromptManager._cached_load_local_template.cache_clear()
        PromptManager._cached_load_supabase_template.cache_clear()
