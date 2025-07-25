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
# Not required if using only local templates
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Path to local templates relative to repo root (optional override)
TEMPLATE_PATH=prompts/templates
```

If `SUPABASE_URL` and `SUPABASE_KEY` are omitted or empty, PromptManager will default to local file loading.

If you are using local file storage for your prompt templates, you do not need a configuration file as the default values will look for templates in ```prompts/templates``` and enable the LRU cache.

You only need to define environment variables if you want to override this behavior.

The *env* file for these values is ```.prompting_env``` and must be in the folder from which you start your app.

Variable Name | Description | Default
---|---|---
SUPABASE_KEY | API key provided by Supabase. If set to None, local file storage is used. | None
SUPABASE_URL | URL provided by Supabase. If set to None, local file storage is used | None
TEMPLATE_PATH | Path, relative to CWD, where local template files are stored. | prompts/templates
USE_CACHE | Determines whether template loading uses an LRU cache to improve performance. | True
FORCE_SOURCE | Can force the template source to be local even if Supabase connection parameters are available. Set to "local" to force local template loading. | ''

The following configuration will look for templates in the Supabase database because both Supabase variables are defined and will *not* use the LRU cache.

```
# .prompting_env
SUPABASE_KEY=api_key_provided_by_supabase
SUPABASE_URL=https://url_provided_by_supabase
TEMPLATE_PATH=app/prompts/templates
USE_CACHE=False  # Good for testing versions of prompt templates. Bad for production performance.
```

---

## 📁 Local File Storage

Place your templates in the directory specified by `template_path` (default is `prompts/templates/`).

Templates must use `.j2` extension and may include [YAML frontmatter](https://jekyllrb.com/docs/front-matter/) metadata.

**Example: `prompts/templates/us_state_prompt.j2`**

```jinja
---
description: Request name of the capital city of a U.S. State
author: Tom Daley
---

What is the capital of {{us_state}}?
```

**Usage:**

```python
from prompting import PromptManager

template = PromptManager.load_template("us_state_prompt")
output = PromptManager.render(template, {"us_state": "TX"})
print(output)
```

 **NOTE:** The ```load_template()``` methods adds a *source* property to the returned object.

---

## 🌐 Supabase Storage

Your Supabase table should be named `prompts` with at least these columns:

| name   | content                | description (optional) | author (optional) |
| ------ | ---------------------- | ---------------------- | ----------------- |
| STRING | TEXT (Jinja2 template) | TEXT                   | TEXT              |

**Example Record:**

| name    | content             | description     | author    |
| ------- | ------------------- | --------------- | --------- |
| us_state_prompt | `What is the capital of the following U.S. State: {{us_state}}` | Request the name of the capital city of a U.S. State | Tom Daley |

**Usage:**

```python
from prompt_manager import PromptManager

template = PromptManager.load_template("us_state_prompt")
output = PromptManager.render(template, {"us_state": "TX"})
print(output)
```

---

## 🧪 Template Metadata

```python
info = PromptManager.template_info(template)
print(info)
# {
#     'name': None,
#     'description': 'Request the name of the capital cit of a U.S. State',
#     'author': 'Tom Daley',
#     'variables': {'us_state'}
# }
```

---

## API Reference

### **.clear_cache()**

*Clear the LRU cache of retrieved templates.*

*Args*: None

*Environment variables*: None

*Returns*: None

*Throws*: Hopefully None


### **.get_supabase_client()**

*Retrieve the Supabase client object.*

*Args*: None

*Environment variables*:
 - SUPABASE_URL - URL provided by Supabase for the project/database that will hold your prompts
 - SUPABASE_KEY - Key provided by Supabase for API access to the project reference by SUPABASE_URL

*Returns*: supabase_client.Client

*Throws*: RuntimeError if Supabase environment variables are not defined.

You should never have to access this method, but it's here in case you need to test your Supabase connection.

### **.load_template(template_name: str)**

*Load a template from either the file system or the database, depending on configuration.*

*Args*:
- *template_name*: str - The name of the template to load. If the Supabase parameters are configured, then this is the value of the 'name' field in the database. If file system storage is being used, this is the name of the template file **without an extension**. The ".j2" extension will be added.

*Environment variables*:
- USE_CACHE - Boolean specifying whether the LRU cache is to be used. Default is True, which is a good setting for production. If you're experimenting with forms of your prompts in development, maybe set it to False so that the latest version of your prompt is picked up each time.

*Returns*: jinja2.Template

*Throws*:
- *ValueError* - If the template cannot be found in the database or on an unspecified error.
- *TemplateError* - If there is an error parsing the template.
- *FileNotFoundError* - If the template is not found in the file system.
- *TemplateNotFoundError* - If the jinja2 template loader throws an error trying to find the template.

This method will call .load_local_template() or .load_supabase_template() based on whether the Supabase environment variables are set. Note that the underlying load_local_template() and load_supabase_template() will add a ```source``` property to the Template object. The ```source``` property contains the source of the template as a string.

## **.template_info(template: Template)**

*Return template metadata.*

*Args*:
- *template* - Instance of Template created by ```load_template()``` or one of its underlying methods.

*Environment variables*: None

*Returns*: Dict[Str, Any] with the following keys:
- name: Template name
- description: Template description if provided in the front matter OR defined in the database.
- author: Author of the template
- variables: List of variables defined in the template.

*Throws*: None

This method provides some descriptive data about the template. Note that the argument to this function is the Template object returned by ```load_template()```, not the template name string.

*WORKS*
```python
template_name = 'test'
template_metadata = PromptManager.template_info(SuperBase.load_template(template_name))

# OR

template = PromptManager.load_template(template_name)
template_metadata = PromptManager.template_info(template)
```

*FAILS*
```python
template_name = 'test'
template_metadata = PromptManager.template_info(template_name)
```

### **.render(template: Template, context: Dict[str, Any])**

*Render a template using the name/value pairs in the context argument.*

*Args*:
- template - Instance of Template created by ```load_template()```.
- context - Python ```dict``` of name/value pairs where the keys are the variables referenced in the template and the values are the values to be substituted in.

*Environment variables*: None

*Returns*: str containing the rendered template with all variable substitutions.

*Throws*: Any exception thrown by Template.render() in the Jinja2 API.

---

## Minimal Working Example

### Step 1: Create your template

Suppose you have a template file with the following content:

```jinja2
---
name: to_do_list
description: Creates a list of 10 things not to do and 10 things to do during pendency of a lawsuit.
author: Thomas J. Daley, Esq.
version: 2025.06.02.001
---

You are a Texas Family Law Litigation Attorney named {{bot_name | default("Tom")}}. You represent a litigant in a {{matter_type}} matter.

Create a list of 10 things your client should *NOT* do while the litigation is pending and then create a list of 10 things that might be important for the judge to know about your client at trial.
```

Relative to your current working directory, save the template as ```prompts/templates/to_do_list.j2```.

### Step 2: Install the PromptManager package

```bash
pip install git+https://github.com/tjdaley/prompting.git
```

### Step 3: Minimal Working Example

Then run this program:

```python
from prompting import PromptManager
template = PromptManager.load_template('to_do_list')
rendition = PromptManager.render(template, context={'matter_type': "Child Custody"})
print(rendition)
```

Output:
```
You are a Texas Family Law Litigation Attorney named Tom. You represent a litigant in a Child Custody matter.

Create a list of 10 things your client should *NOT* do while the litigation is pending and then create a list of 10 things that might be important for the judge to know about your client at trial.
```

That's all there is to it!!

---

## 🧰 License

MIT License © [Tom Daley](https://github.com/tjdaley)

## Author

Thomas J. Daley is a board certified Texas Family Law Litigation attorney and AI enthusiast.
[BLOG](https://www.thomasjdaley.com) * [LINKEDIN](https://www.linkedin.com/in/tomdaley/) * [LAW FIRM](https://koonsfuller.com/attorneys/tom-daley)
