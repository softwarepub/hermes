{#
SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf
SPDX-License-Identifier: CC-BY-SA-4.0
SPDX-FileContributor: David Pape
#}

{% for step in ("harvest", "process", "curate", "deposit", "postprocess") %}

### {{ step|title }}

<ul>
{%- for plugin in data -%}
  {%- if step in plugin.steps -%}
  <li style="margin-top: 0.5rem;">
    {%- if plugin.repository_url -%}
    <a href="{{ plugin.repository_url }}" rel="nofollow">{{ plugin.name }}</a>
    {%- else -%}
    {{ plugin.name }}
    {%- endif -%}
    <span style="color: gray;"> by <em>{{ plugin.author }}</em><br></span>
    {%- if plugin.description -%}
    {{ plugin.description }}<br>
    {%- endif -%}
    {%- if plugin.builtin -%}
    <span style="color: gray;">This plugin is built into Hermes.</span><br>
    {%- elif plugin.pypi_url -%}
    <span style="color: gray;">Install via <a href="{{ plugin.pypi_url }}">PyPI</a>.</span><br>
    {%- endif -%}
  </li>
  {%- endif -%}
{%- endfor -%}
</ul>
{% endfor %}
