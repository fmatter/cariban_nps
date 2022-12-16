{% import 'html_util.md' as util %}
{% if ids is defined %}
    {% set ids = ids.split(",") %}
    {% set gathered_examples = {} %}
    {% set lgs = [] %}
    {% for example in ctx %}
        {% if example.id in ids %}
            {% set _ = gathered_examples.update({example.id: example}) %}
            {% if example.language.id not in lgs %}
                {% set _ = lgs.append(example.language.id) %}
            {% endif %}
        {% endif %}
    {% endfor %}
```{=html}
<ol class="example">
    <li class="example" id="{{example_id}}">
        <ol class="subexample">
            {% for example_id in ids %}
                {% if loop.index > 1 and lgs|length == 1 %}
                {{ util.example(gathered_examples[example_id], class_="subexample", show_lg=False) }}                
                {% else %}
                {{ util.example(gathered_examples[example_id], class_="subexample") }}
                {%endif %}
            {% endfor %}
        </ol>
    </li>
</ol>
```
{% endif %}
