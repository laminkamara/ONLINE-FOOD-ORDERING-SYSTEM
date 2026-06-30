#!/usr/bin/env python
"""
Comprehensive template and template tag audit script.
Identifies missing load statements, syntax errors, and template tag issues.
"""

import os
import re
import sys
from pathlib import Path
from django.conf import settings
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')
django.setup()

from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from django.templatetags.base import Library

def find_all_templates():
    """Find all template files in the project."""
    template_dir = Path('core/templates')
    templates = list(template_dir.rglob('*.html'))
    return templates

def check_template_syntax(template_path):
    """Check if template has valid syntax."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Try to compile the template
        Template(content)
        return True, None
    except TemplateSyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def find_filters_used(template_path):
    """Find all custom filters used in the template."""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all filter usages: |filter_name
    filters = re.findall(r'\|(\w+)', content)
    return set(filters)

def find_load_statements(template_path):
    """Find all {% load %} statements in the template."""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all load statements
    loads = re.findall(r'{%\s*load\s+([\w\s]+)\s*%}', content)
    loaded_tags = set()
    for load in loads:
        tags = load.split()
        loaded_tags.update(tags)
    return loaded_tags

def get_custom_filters():
    """Get list of all custom filters available."""
    try:
        from core.templatetags import custom_filters
        filters = []
        for name in dir(custom_filters):
            obj = getattr(custom_filters, name)
            if hasattr(obj, '_decorated_function'):  # It's a filter
                filters.append(name)
        return filters
    except Exception as e:
        print(f"Error loading custom filters: {e}")
        return []

def main():
    print("=" * 80)
    print("TEMPLATE AND TEMPLATE TAG AUDIT")
    print("=" * 80)
    
    templates = find_all_templates()
    print(f"\nFound {len(templates)} templates\n")
    
    custom_filters = get_custom_filters()
    print(f"Available custom filters: {custom_filters}\n")
    
    issues = []
    
    for template_path in sorted(templates):
        print(f"Checking: {template_path}")
        
        # Check syntax
        is_valid, error = check_template_syntax(template_path)
        if not is_valid:
            issues.append({
                'file': str(template_path),
                'type': 'SYNTAX_ERROR',
                'message': error
            })
            print(f"  ❌ SYNTAX ERROR: {error}")
            continue
        
        # Find filters used
        filters_used = find_filters_used(template_path)
        
        # Find load statements
        loaded = find_load_statements(template_path)
        
        # Check if custom filters are loaded when needed
        used_custom_filters = filters_used & set(custom_filters)
        if used_custom_filters and 'custom_filters' not in loaded:
            issues.append({
                'file': str(template_path),
                'type': 'MISSING_LOAD',
                'message': f'Uses custom filters {used_custom_filters} but missing load statement'
            })
            print(f"  ⚠️  MISSING LOAD: Uses custom filters but no load statement")
        
        if is_valid and not issues[-1:]:
            print(f"  ✅ OK")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issues:\n")
        for issue in issues:
            print(f"  {issue['type']}: {issue['file']}")
            print(f"    Message: {issue['message']}\n")
    else:
        print("\n✅ No issues found!")
    
    # Try to load a problematic template
    print("\n" + "=" * 80)
    print("TESTING TEMPLATE LOADING")
    print("=" * 80)
    
    test_templates = [
        'core/manage_menu.html',
        'core/cart.html',
        'core/checkout.html',
    ]
    
    for template_name in test_templates:
        try:
            print(f"\nLoading: {template_name}")
            template = get_template(template_name)
            print(f"  ✅ Loaded successfully")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

if __name__ == '__main__':
    main()
