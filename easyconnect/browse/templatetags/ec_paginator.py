from django import template

register = template.Library()

@register.inclusion_tag('browse/ec_paginator.html', takes_context=True)
def ec_paginator(context, adjacent=2):
    page = context['page']
    paginator = context['paginator']

    num_pages = paginator.num_pages

    paginator.sort_methods = {
        "date",
        "name"
    }
    
    startPage = max(page.number - adjacent, 1)
    if startPage <= 3: startPage = 1
    endPage = page.number + adjacent + 1
    if endPage >= num_pages - 1: endPage = num_pages + 1
    page_numbers = [n for n in range(startPage, endPage) if n > 0 and n <= num_pages]

    return {
        'paginator': paginator,
        'page': page,
        'page_numbers': page_numbers,
        'show_first': 1 not in page_numbers,
        'show_last': num_pages not in page_numbers,
        'context': context,
    }
