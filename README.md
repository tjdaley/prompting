# Prompt Manager

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub](https://img.shields.io/badge/source-github.com/tjdaley/prompting-black)

**Prompt Manager** is a lightweight Python library that abstracts the retrieval and rendering of prompt templates using Jinja2. Templates can be stored locally or remotely in Supabase, with zero changes required in your code.

---

## 🚀 Features

- 🔄 Load prompt templates from:
  - Local `.j2` files with optional frontmatter
  - Supabase table (`prompts`)
- ⚙️ Unified API for both sources
- 🧠 Template rendering with Jinja2
- 💾 Smart caching of recently-used prompts
- 🔍 Extract prompt metadata and undeclared variables

---

## 📦 Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/tjdaley/prompting.git
````

---

## ⚙️ Configuration: `.prompting_env`

Create a `.prompting_env` file in the root of your project (or wherever your Python process starts) with the following variables:

```env
# Optional if using only local templates
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Path to local templates relative to repo root (optional override)
TEMPLATE_PATH=prompts/templates
```

If `SUPABASE_URL` and `SUPABASE_KEY` are omitted or empty, PromptManager will default to local file loading.

---

## 📁 Local File Storage

Place your templates in the directory specified by `template_path` (default is `prompts/templates/`).

Templates must use `.j2` extension and may include [YAML frontmatter](https://jekyllrb.com/docs/front-matter/) metadata.

**Example: `prompts/templates/welcome.j2`**

```jinja
---
description: Welcome message for new users
author: Tom Daley
---

Hello {{ name }}! Welcome to the platform.
```

**Usage:**

```python
from prompt_manager import PromptManager

template = PromptManager.load_template("welcome")
output = PromptManager.render_template(template, {"name": "Tom"})
print(output)
```

---

## 🌐 Supabase Storage

Your Supabase table should be named `prompts` with at least these columns:

| name   | content                | description (optional) | author (optional) |
| ------ | ---------------------- | ---------------------- | ----------------- |
| STRING | TEXT (Jinja2 template) | TEXT                   | TEXT              |

**Example Record:**

| name    | content             | description     | author    |
| ------- | ------------------- | --------------- | --------- |
| welcome | `Hello {{ name }}!` | Welcome message | Tom Daley |

**Usage:**

```python
from prompt_manager import PromptManager

template = PromptManager.load_template("welcome")
output = PromptManager.render_template(template, {"name": "Tom"})
print(output)
```

---

## 🧪 Template Metadata

```python
info = PromptManager.template_info(template)
print(info)
# {
#     'name': None,
#     'description': 'Welcome message for new users',
#     'author': 'Tom Daley',
#     'variables': {'name'}
# }
```

---

## 🧰 License

MIT License © [Tom Daley](https://github.com/tjdaley)

