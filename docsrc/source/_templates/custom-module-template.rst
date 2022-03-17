{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

   {% block functions %}
   {% if functions %}
   .. autosummary::
      :toctree:
   {% for item in functions %}
   {% if item == "click_main" %}
   .. click:: {{ fullname }}:{{ name }}
      :prog: {{ name }}
      :nested: full
   {% else %}
   ********************
   {{ name }}
   ********************
   .. parsed-literal::
      {{ name }}
   {% endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}

{% block modules %}
{% if modules %}
.. rubric:: Modules

.. autosummary::
   :toctree:
   :template: custom-module-template.rst
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}