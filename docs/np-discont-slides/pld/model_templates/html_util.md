{% macro example(ctx, class_="example", example_id=None, highlight=[], show_lg=True) -%}
{% if ctx.references %}
{% set ref = ctx.references[0] %}
{% set bibkey, pages = split_ref(ref.__str__()) %}
{% set audio = get_audio(ctx.id) %}
<!--[{{bibkey}}](sources.bib?with_internal_ref_link&ref#cldf:{{bibkey}})"-->
{% endif %}
<li class={{class_}} id ="{{ example_id or ctx.id }}">
  <div class="interlinear">
    {% if show_lg %}
        {{ ctx.related("languageReference").name }}
    {% endif %}
      <div class="surf">{{ ctx.cldf.primaryText }}</div>
    {% if ctx.cldf.analyzedWord != [] %}
      {% for obj in ctx.cldf.analyzedWord %}
        <div class="intlin">
          <span class="obj">{{ obj.replace("**", "<b>", 1).replace("**", "</b>", 1) }}</span>
          <span class="trans">{{ decorate_gloss_string(ctx.cldf.gloss[loop.index-1])}}</span>
          <span class="pos">{{ ctx.data["Part_Of_Speech"][loop.index-1] }}</span>
        </div>
      {% endfor %}
    {% endif %}
    <div class="freetrans">‘{{ ctx.cldf.translatedText }}’ {% if ref %}({{ref.source.refkey(year_brackets=None)}}{%if ref.description%}: {{ref.description}}{%endif%})
        {%endif%}
        </div>
        {% if audio %}
            <audio controls>
                <source src={{ audio["url"] }} type="audio/{{ audio["type"]}}"> 
            </audio> 
        {% endif %}
  </div>
</li>
{%- endmacro %}